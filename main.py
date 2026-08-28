
import os
import time
import joblib
import shap
import pandas as pd
import requests

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# ============================================================
# CREATE FASTAPI APP
# ============================================================

app = FastAPI(
    title="MindWell AI API",
    description="Mental Wellness Prediction + SHAP + AI Chatbot",
    version="1.0"
)


# ============================================================
# ENABLE CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# MODEL PATH
# ============================================================

MODEL_PATH = r"C:\Users\Alyna\Downloads\jupyterpractice\Mental_Health_Model.pkl"

print("MODEL PATH:", MODEL_PATH)
print("MODEL EXISTS:", os.path.exists(MODEL_PATH))


# ============================================================
# LOAD MODEL
# ============================================================

try:
    model = joblib.load(MODEL_PATH)
    print("Model loaded successfully!")

except Exception as e:
    print("MODEL LOADING ERROR:", str(e))
    raise RuntimeError(
        f"Could not load model from: {MODEL_PATH}"
    ) from e


# ============================================================
# GET PREPROCESSOR AND RANDOM FOREST
# ============================================================

try:
    print("PIPELINE STEP NAMES:")
    print(model.named_steps.keys())

    preprocessor = model.named_steps["preprocessor"]
    regressor = model.named_steps["random forest"]

    print("Preprocessor extracted successfully!")
    print("Random Forest extracted successfully!")

except Exception as e:
    print("PIPELINE ERROR:", str(e))
    raise RuntimeError(
        "Could not find preprocessor or random forest in saved pipeline."
    ) from e


# ============================================================
# ORIGINAL COLUMNS
# ============================================================

skewed_cols = [
    "Study_Hours"
]

other_numeric_cols = [
    "Age",
    "Sleep_Hours_Per_Night",
    "Daily_Unlocks",
    "Physical_Activity_Hours",
    "Avg_Daily_Usage_Hours"
]

ordinal_col = [
    "Stress_Level"
]

normal_cols = [
    "Gender",
    "Most_Used_Platform",
    "grouped_countries",
    "Purpose_Of_Use",
    "Academic_Level"
]


# ============================================================
# CREATE FEATURE NAMES FOR SHAP
# ============================================================

feature_names = []

feature_names.extend(skewed_cols)
feature_names.extend(other_numeric_cols)
feature_names.extend(ordinal_col)


try:
    nominal_transformer = preprocessor.named_transformers_[
        "Normal Pipeline"
    ]

    onehot_encoder = nominal_transformer.named_steps[
        "encode"
    ]

    onehot_feature_names = onehot_encoder.get_feature_names_out(
        normal_cols
    )

    feature_names.extend(
        list(onehot_feature_names)
    )

except Exception as e:
    print("FEATURE NAME ERROR:", str(e))
    raise RuntimeError(
        "Could not create SHAP feature names."
    ) from e


print("Number of SHAP feature names:", len(feature_names))


# ============================================================
# CREATE SHAP EXPLAINER ONCE
# ============================================================

try:
    explainer = shap.TreeExplainer(regressor)
    print("SHAP explainer created successfully!")

except Exception as e:
    print("SHAP ERROR:", str(e))
    raise RuntimeError(
        "Could not create SHAP explainer."
    ) from e


# ============================================================
# INPUT MODEL FOR PREDICTION
# ============================================================

class MentalHealthInput(BaseModel):

    Age: float
    Gender: str
    Sleep_Hours_Per_Night: float
    Daily_Unlocks: float
    Physical_Activity_Hours: float
    Avg_Daily_Usage_Hours: float
    Study_Hours: float
    Stress_Level: str
    Most_Used_Platform: str
    grouped_countries: str
    Purpose_Of_Use: str
    Academic_Level: str


# ============================================================
# INPUT MODEL FOR CHATBOT
# ============================================================

class ChatInput(BaseModel):

    message: str
    prediction_context: dict | None = None


# ============================================================
# CHATBOT SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are MindWell AI, a supportive AI assistant for a Mental Wellness
Prediction and Explainable AI project.

You can:
- Explain mental wellness predictions in simple language.
- Explain SHAP factors.
- Answer general questions about sleep, stress, screen time,
  physical activity, digital wellbeing and healthy routines.

Important rules:
- Do not diagnose mental health conditions.
- Do not claim the prediction is a medical diagnosis.
- SHAP factors explain how the machine learning model reached its
  prediction and do not prove real-world causation.
- Be supportive, practical and easy to understand.
- Do not present yourself as a doctor or therapist.
- If immediate danger, suicide or self-harm is mentioned, encourage
  the user to contact emergency services, crisis support or a trusted
  person nearby immediately.

Keep answers concise and human-friendly.
"""


# ============================================================
# MAKE FEATURE NAMES HUMAN READABLE
# ============================================================

def make_feature_readable(feature):

    feature = str(feature)

    feature = feature.replace("_", " ")

    feature = feature.replace(
        "Avg Daily Usage Hours",
        "Average Daily Usage Hours"
    )

    feature = feature.replace(
        "grouped countries",
        "Country"
    )

    return feature


# ============================================================
# CREATE FACTOR EXPLANATION
# ============================================================

def create_factor_explanation(feature, direction):

    feature = make_feature_readable(feature)

    if direction == "lower":

        return (
            f"{feature} was one of the factors that pushed "
            f"the machine learning model's predicted score lower."
        )

    return (
        f"{feature} was one of the factors that pushed "
        f"the machine learning model's predicted score higher."
    )


# ============================================================
# CREATE RECOMMENDATION
# ============================================================

def create_recommendation(feature):

    feature = feature.lower()

    if "sleep" in feature:

        return (
            "Consider maintaining a consistent sleep routine and "
            "reviewing habits that may affect sleep quality."
        )

    elif "usage" in feature:

        return (
            "Consider reviewing daily screen time and taking regular "
            "breaks from digital devices."
        )

    elif "unlock" in feature:

        return (
            "Consider reducing unnecessary notifications and "
            "frequent phone checking."
        )

    elif "physical" in feature:

        return (
            "Consider maintaining regular physical activity that "
            "fits comfortably into your daily routine."
        )

    elif "stress" in feature:

        return (
            "Consider identifying major sources of stress and using "
            "healthy coping strategies such as breaks, exercise, "
            "relaxation, or talking with someone you trust."
        )

    elif "study" in feature:

        return (
            "Try to maintain a balanced study routine with regular "
            "breaks and adequate rest."
        )

    elif "platform" in feature:

        return (
            "Consider reflecting on your social media habits and "
            "taking regular breaks when needed."
        )

    else:

        return (
            "Consider reviewing this factor as part of your overall "
            "daily routine and wellbeing."
        )


# ============================================================
# HOME ENDPOINT
# ============================================================

@app.get("/")
def home():

    return {
        "message": "MindWell AI API is running successfully!"
    }


# ============================================================
# PREDICTION ENDPOINT WITH TIMING
# ============================================================

@app.post("/predict")
def predict(data: MentalHealthInput):

    try:

        # START TOTAL TIMER
        total_start = time.time()


        # ----------------------------------------------------
        # CREATE INPUT DATAFRAME
        # ----------------------------------------------------

        input_data = pd.DataFrame(
            [data.model_dump()]
        )

        dataframe_time = time.time()


        # ----------------------------------------------------
        # MAKE PREDICTION
        # ----------------------------------------------------

        prediction = float(
            model.predict(input_data)[0]
        )

        prediction = round(
            prediction,
            2
        )

        prediction_time = time.time()

        print(
            "Prediction step:",
            round(
                prediction_time - dataframe_time,
                4
            ),
            "seconds"
        )


        # ----------------------------------------------------
        # TRANSFORM INPUT FOR SHAP
        # ----------------------------------------------------

        transformed_input = preprocessor.transform(
            input_data
        )

        if hasattr(
            transformed_input,
            "toarray"
        ):

            transformed_input = (
                transformed_input.toarray()
            )

        transform_time = time.time()

        print(
            "Preprocessing step:",
            round(
                transform_time - prediction_time,
                4
            ),
            "seconds"
        )


        # ----------------------------------------------------
        # CALCULATE SHAP VALUES
        # ----------------------------------------------------

        shap_values = explainer.shap_values(
            transformed_input
        )

        shap_time = time.time()

        print(
            "SHAP calculation:",
            round(
                shap_time - transform_time,
                4
            ),
            "seconds"
        )


        # ----------------------------------------------------
        # HANDLE SINGLE PREDICTION
        # ----------------------------------------------------

        if len(shap_values.shape) > 1:

            shap_values = shap_values[0]


        # ----------------------------------------------------
        # COMBINE FEATURES WITH SHAP VALUES
        # ----------------------------------------------------

        feature_impacts = []

        for feature, impact in zip(
            feature_names,
            shap_values
        ):

            feature_impacts.append(
                {
                    "factor": make_feature_readable(feature),
                    "impact": round(float(impact), 4)
                }
            )


        # ----------------------------------------------------
        # FACTORS LOWERING PREDICTION
        # ----------------------------------------------------

        lowering_factors = [

            item for item in feature_impacts

            if item["impact"] < 0

        ]


        lowering_factors = sorted(
            lowering_factors,
            key=lambda x: x["impact"]
        )[:5]


        for item in lowering_factors:

            item["explanation"] = (
                create_factor_explanation(
                    item["factor"],
                    "lower"
                )
            )

            item["recommendation"] = (
                create_recommendation(
                    item["factor"]
                )
            )


        # ----------------------------------------------------
        # FACTORS INCREASING PREDICTION
        # ----------------------------------------------------

        increasing_factors = [

            item for item in feature_impacts

            if item["impact"] > 0

        ]


        increasing_factors = sorted(
            increasing_factors,
            key=lambda x: x["impact"],
            reverse=True
        )[:5]


        for item in increasing_factors:

            item["explanation"] = (
                create_factor_explanation(
                    item["factor"],
                    "higher"
                )
            )


        # ----------------------------------------------------
        # CREATE SUMMARY
        # ----------------------------------------------------

        if lowering_factors:

            strongest_factor = (
                lowering_factors[0]["factor"]
            )

            summary = (
                f"The predicted mental wellness score is "
                f"{prediction}. The strongest factor pushing "
                f"this particular model prediction lower was "
                f"{strongest_factor}."
            )

        else:

            summary = (
                f"The predicted mental wellness score is "
                f"{prediction}."
            )


        # ----------------------------------------------------
        # TOTAL TIME
        # ----------------------------------------------------

        total_end = time.time()

        total_time = round(
            total_end - total_start,
            4
        )

        print(
            "TOTAL PREDICT TIME:",
            total_time,
            "seconds"
        )


        # ----------------------------------------------------
        # RETURN RESULT
        # ----------------------------------------------------

        return {

            "predicted_mental_health_score": prediction,

            "summary": summary,

            "factors_lowering_prediction": lowering_factors,

            "factors_increasing_prediction": increasing_factors,

            "processing_time_seconds": total_time,

            "disclaimer": (
                "These explanations describe how the machine learning "
                "model arrived at its prediction. They do not establish "
                "medical or real-world causation and are not a clinical "
                "diagnosis."
            )
        }


    except Exception as e:

        print(
            "PREDICTION ERROR:",
            str(e)
        )

        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


# ============================================================
# CHATBOT ENDPOINT
# ============================================================

@app.post("/chat")
def chat_with_mindwell(data: ChatInput):

    try:

        user_message = data.message.strip()


        if not user_message:

            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty."
            )


        # ----------------------------------------------------
        # ADD PREDICTION CONTEXT
        # ----------------------------------------------------

        context = ""

        if data.prediction_context:

            context = f"""

USER'S LATEST PREDICTION CONTEXT:

{data.prediction_context}

Use this information only when relevant.
Do not invent information that is not provided.
"""


        # ----------------------------------------------------
        # CREATE PROMPT
        # ----------------------------------------------------

        full_prompt = f"""
{SYSTEM_PROMPT}

{context}

USER QUESTION:
{user_message}

Respond as MindWell AI:
"""


        # ----------------------------------------------------
        # CALL OLLAMA
        # ----------------------------------------------------

        response = requests.post(

            "http://127.0.0.1:11434/api/generate",

            json={
                "model": "llama3.2",
                "prompt": full_prompt,
                "stream": False
            },

            timeout=180
        )


        response.raise_for_status()


        result = response.json()


        chatbot_response = result.get(
            "response",
            "Sorry, I could not generate a response."
        )


        return {

            "response": chatbot_response.strip(),

            "disclaimer": (
                "MindWell AI provides general information and "
                "explains machine learning predictions. It is not "
                "a substitute for professional mental health care "
                "or a clinical diagnosis."
            )
        }


    except HTTPException:

        raise


    except requests.exceptions.ConnectionError:

        raise HTTPException(
            status_code=503,
            detail=(
                "Could not connect to Ollama. Make sure Ollama "
                "is installed and running."
            )
        )


    except requests.exceptions.Timeout:

        raise HTTPException(
            status_code=504,
            detail="The AI model took too long to respond."
        )


    except Exception as e:

        print(
            "CHATBOT ERROR:",
            str(e)
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )