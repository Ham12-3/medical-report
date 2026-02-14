"""Mock data for demo mode — realistic chest X-ray findings pipeline."""

import asyncio
import random


async def demo_delay() -> None:
    """Simulate API latency (1-2 seconds)."""
    await asyncio.sleep(random.uniform(1.0, 2.0))


def get_demo_findings() -> list[dict]:
    """Return realistic chest X-ray findings."""
    return [
        {
            "finding": "Cardiomegaly",
            "location": "Cardiac silhouette",
            "severity": "medium",
            "confidence": 0.89,
            "details": (
                "The cardiac silhouette is enlarged with a cardiothoracic ratio "
                "of approximately 0.58, exceeding the normal threshold of 0.50. "
                "This suggests mild to moderate cardiomegaly."
            ),
        },
        {
            "finding": "Pleural Effusion",
            "location": "Right costophrenic angle",
            "severity": "low",
            "confidence": 0.76,
            "details": (
                "Blunting of the right costophrenic angle is noted, consistent "
                "with a small right-sided pleural effusion. No layering is "
                "observed on the lateral view."
            ),
        },
        {
            "finding": "Pulmonary Nodule",
            "location": "Right upper lobe",
            "severity": "high",
            "confidence": 0.72,
            "details": (
                "A 12 mm well-circumscribed nodule is identified in the right "
                "upper lobe. No calcification or cavitation is apparent. "
                "Follow-up imaging is recommended per Fleischner Society guidelines."
            ),
        },
    ]


def get_demo_research(findings: list[dict]) -> list[dict]:
    """Return mock research results keyed to each finding."""
    _refs = {
        "Cardiomegaly": [
            {
                "id": "ref-cardio-001",
                "score": 0.94,
                "text": (
                    "Defined as a cardiothoracic ratio >0.50 on PA chest "
                    "radiograph. Common aetiologies include hypertensive heart "
                    "disease, valvular disease, and dilated cardiomyopathy."
                ),
                "source_file": "Harrison's Principles of Internal Medicine, 21e",
                "query_used": "cardiomegaly diagnostic criteria chest radiograph",
            },
            {
                "id": "ref-cardio-002",
                "score": 0.88,
                "text": (
                    "Echocardiography is the recommended next step for "
                    "evaluating cardiomegaly detected on chest X-ray to "
                    "assess chamber dimensions and ventricular function."
                ),
                "source_file": "ACC/AHA Guidelines 2023",
                "query_used": "cardiomegaly workup echocardiography",
            },
        ],
        "Pleural Effusion": [
            {
                "id": "ref-effusion-001",
                "score": 0.91,
                "text": (
                    "Small pleural effusions may be detected on chest X-ray "
                    "as blunting of the costophrenic angle, typically requiring "
                    ">200 mL of fluid to be visible on PA view."
                ),
                "source_file": "Radiopaedia - Pleural Effusion",
                "query_used": "pleural effusion chest x-ray detection threshold",
            },
        ],
        "Pulmonary Nodule": [
            {
                "id": "ref-nodule-001",
                "score": 0.93,
                "text": (
                    "Solitary pulmonary nodules 6-8 mm in low-risk patients "
                    "should be followed with CT at 6-12 months; nodules >8 mm "
                    "warrant CT at 3 months, PET/CT, or tissue sampling."
                ),
                "source_file": "Fleischner Society 2017 Guidelines",
                "query_used": "pulmonary nodule follow-up Fleischner guidelines",
            },
            {
                "id": "ref-nodule-002",
                "score": 0.87,
                "text": (
                    "Risk factors for malignancy include size >15 mm, "
                    "spiculated margins, upper-lobe location, and patient "
                    "age >65 years or smoking history."
                ),
                "source_file": "ACCP Evidence-Based Guidelines",
                "query_used": "pulmonary nodule malignancy risk factors",
            },
        ],
    }

    results = []
    for f in findings:
        name = f.get("finding", "unknown")
        results.append(
            {
                "finding": name,
                "search_queries": [
                    f"{name} clinical guidelines",
                    f"{name} medical literature",
                ],
                "references": _refs.get(name, []),
            }
        )
    return results


def get_demo_report() -> dict:
    """Return a realistic structured diagnostic report."""
    return {
        "executive_summary": (
            "Chest radiograph analysis reveals three findings of clinical "
            "significance: mild-to-moderate cardiomegaly, a small right-sided "
            "pleural effusion, and a 12 mm solitary pulmonary nodule in the "
            "right upper lobe. The pulmonary nodule warrants the most urgent "
            "follow-up given its size and location."
        ),
        "detailed_findings": [
            {
                "finding": "Cardiomegaly",
                "explanation": (
                    "The cardiac silhouette is enlarged with a cardiothoracic "
                    "ratio of approximately 0.58. This finding is consistent "
                    "with mild-to-moderate cardiomegaly and may be associated "
                    "with hypertensive heart disease, valvular pathology, or "
                    "dilated cardiomyopathy."
                ),
                "supporting_literature": (
                    "ACC/AHA guidelines recommend echocardiography as the "
                    "primary follow-up modality for cardiomegaly detected on "
                    "chest radiograph."
                ),
            },
            {
                "finding": "Pleural Effusion",
                "explanation": (
                    "A small right-sided pleural effusion is suggested by "
                    "blunting of the right costophrenic angle. The effusion "
                    "appears to be free-flowing without loculation."
                ),
                "supporting_literature": (
                    "Small effusions visible on PA radiograph typically "
                    "represent >200 mL of fluid. Lateral decubitus views or "
                    "ultrasound can confirm and quantify the effusion."
                ),
            },
            {
                "finding": "Pulmonary Nodule",
                "explanation": (
                    "A 12 mm well-circumscribed nodule in the right upper lobe "
                    "requires further evaluation. The absence of calcification "
                    "increases the index of suspicion, though the smooth margins "
                    "are a reassuring feature."
                ),
                "supporting_literature": (
                    "Per Fleischner Society 2017 guidelines, nodules >8 mm "
                    "warrant CT follow-up at 3 months, PET/CT evaluation, or "
                    "tissue sampling depending on clinical risk factors."
                ),
            },
        ],
        "risk_assessment": {
            "overall_risk_level": "moderate",
            "confidence_score": 0.79,
            "key_risk_factors": [
                "Solitary pulmonary nodule >8 mm without calcification",
                "Upper-lobe location associated with higher malignancy risk",
                "Cardiomegaly suggesting possible underlying cardiac disease",
            ],
        },
        "recommended_next_steps": [
            "CT chest with contrast within 3 months to characterise the pulmonary nodule",
            "Echocardiography to evaluate cardiac chamber dimensions and function",
            "Lateral decubitus chest X-ray or thoracic ultrasound to quantify the pleural effusion",
            "Clinical correlation with patient history, symptoms, and risk factors",
            "Referral to pulmonology if nodule is confirmed on CT",
        ],
        "metadata": {
            "generated_at": "2026-02-14T00:00:00Z",
            "model_used": "demo-mode",
            "disclaimer": (
                "This report was generated by an AI system operating in demo "
                "mode with simulated data. It is for demonstration purposes "
                "only and must NOT be used for clinical decision-making."
            ),
        },
    }


def get_demo_safety_review() -> dict:
    """Return a realistic safety review result."""
    return {
        "flagged_issues": [
            {
                "severity": "low",
                "description": (
                    "Report uses appropriately hedged language but should "
                    "emphasise that AI-generated findings require radiologist "
                    "confirmation."
                ),
                "source": "llm_review",
            },
        ],
        "adjusted_confidence_score": 0.75,
        "recommended_disclaimers": [
            "This report is generated by an AI system and is intended for informational purposes only.",
            "All findings must be reviewed and confirmed by a qualified radiologist or physician.",
            "Do not use this report as the sole basis for clinical decision-making.",
            "AI confidence scores reflect model certainty, not clinical probability of disease.",
        ],
        "safety_passed": True,
    }
