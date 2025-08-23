# services/intent_service.py
from typing import Dict, List, Optional, Union  # Union 추가
import numpy as np
from sentence_transformers import SentenceTransformer

# 모델 및 리소스
DEVICE = "cpu"  # GPU 사용 시 "cuda:0"
MODEL_NAME = "intfloat/multilingual-e5-small"
model = SentenceTransformer(MODEL_NAME, device=DEVICE)

def embed_queries(texts: List[str]) -> np.ndarray:
    texts = [f"query: {t.strip()}" for t in texts]
    return model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)

def embed_passages(texts: List[str]) -> np.ndarray:
    texts = [f"passage: {t.strip()}" for t in texts]
    return model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)

FUNCTION_EXAMPLES: Dict[str, List[str]] = {
    "check_registry": [
        "전세 계약 전에 뭘 확인해야 해?", "체크리스트 보여줘", "계약 중 체크리스트",
        "계약 후 확인사항 알려줘", "준비물 확인", "계약 단계별 확인 사항",
        "전·중·후 점검 리스트", "사전 점검 목록"
    ],
    "risk_assessment": [
        "이 매물 위험도 평가해줘", "보증사고 가능성 알려줘", "전세사기 위험도 분석",
        "내 정보 넣고 위험도 예측", "리스크 계산", "위험 확률",
        "확률로 평가해줘", "모델로 위험 판정"
    ],
    "quiz": [
        "전세사기 퀴즈 풀래", "지식 테스트", "문제 내줘", "학습 퀴즈 시작",
        "퀴즈로 공부할래", "OX 문제"
    ],
    "myhouse": [
        "적정 전세가 확인할래", "매매가로 전세가 예측", "우리 집 전세가 예측"
    ]
}

FUNCTION_DESCRIPTIONS: Dict[str, str] = {
    "check_registry": "전세 계약 전/중/후 단계별 체크리스트를 안내합니다.",
    "risk_assessment": "입력한 매물 정보로 전세사기 위험도를 예측합니다.",
    "quiz": "퀴즈로 전세 안전지식을 테스트하고 학습합니다.",
    "myhouse": "매매가로 해당 시도의 적정 전세가를 예측합니다."
}

KEYWORD_PRIORS: Dict[str, List[str]] = {
    "risk_assessment": ["위험", "리스크", "확률", "예측", "평가", "모델"],
    "quiz": ["퀴즈", "문제", "테스트", "학습", "OX"],
    "check_registry": ["체크", "확인사항", "체크리스트", "점검", "준비물", "전", "중", "후"],
    "myhouse": ["적정", "보증금", "매매가", "전세가"]
}

FUNC_NAMES = list(FUNCTION_EXAMPLES.keys())

# 임베딩 사전 계산
example_bank = {f: embed_passages(FUNCTION_EXAMPLES[f]) for f in FUNC_NAMES}
desc_embs = {f: embed_passages([FUNCTION_DESCRIPTIONS[f]])[0] for f in FUNC_NAMES}

def prior_boost(utterance: str) -> Dict[str, float]:
    u = utterance.replace(" ", "")
    boosts = {f: 0.0 for f in FUNC_NAMES}
    for f, kws in KEYWORD_PRIORS.items():
        for kw in kws:
            if kw in u:
                boosts[f] += 0.03
    return boosts

def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))  # 이미 정규화됨

def rank_functions(user_text: str, top_k: int = 3) -> Dict[str, float]:
    q = embed_queries([user_text])[0]
    sims_knn = {}
    for f in FUNC_NAMES:
        sims = example_bank[f] @ q
        topk = np.sort(sims)[-top_k:]
        sims_knn[f] = float(topk.mean())
    sims_desc = {f: cosine(q, desc_embs[f]) for f in FUNC_NAMES}
    boosts = prior_boost(user_text)
    final_scores = {f: sims_knn[f]*0.7 + sims_desc[f]*0.25 + boosts[f]*1.0 for f in FUNC_NAMES}
    return final_scores

def route_intent(user_text: str,
                 sim_threshold: float = 0.55,
                 margin: float = 0.05,
                 top_k: int = 3) -> Dict[str, Optional[Union[str, float, bool, Dict]]]:
    if not user_text.strip():
        return {
            "text": user_text,
            "matched": False,
            "function": None,
            "best_score": 0.0,
            "second_best": 0.0,
            "scores": {}
        }
    scores = rank_functions(user_text, top_k=top_k)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_func, best_score = ranked[0]
    second_func, second_score = ranked[1] if len(ranked) > 1 else (None, -1.0)
    matched = (best_score >= sim_threshold) and ((best_score - second_score) >= margin)

    return {
        "text": user_text,
        "matched": matched,
        "function": best_func if matched else None,
        "best_score": best_func,      # 숫자가 아닌 이름
        "second_best": second_func,    # 숫자가 아닌 이름
        "scores": dict(ranked)
    }