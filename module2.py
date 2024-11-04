import google.generativeai as genai

genai.configure(api_key="AIzaSyAQoHsGXzf8SiTlZft1L2DZoBfDld6OKb0")  # Replace with your actual API key
model = genai.GenerativeModel("gemini-1.5-flash")

def prepare_database_ready_answers(lab_values_output):
    prompt = """Given a JSON input containing lab values and their associated relational operators, extract and transform only the "Absolute neutrophil count (ANC) or absolute granulocyte count required" based on the specified ANC transformation logic.

Transformation Rules:

1. Identify the relational operator and value for "Absolute neutrophil count (ANC) or absolute granulocyte count required."
2. Apply the transformation rules based on the relational operator, mapping to a standard range of [0.0, 9.9].

Relational Operator Transformations:
- If the operator is "greater than" (`>`), convert to the range [value + 0.1, 9.9].
- If the operator is "greater than or equal to" (`>=`), convert to [value, 9.9].
- If the operator is "less than" (`<`), convert to [0.0, value - 0.1].
- If the operator is "less than or equal to" (`<=`), convert to [0.0, value].

Additional Instructions:
- If no ANC entry is present, return None.
- Convert any units to the standard x10^9/L where needed.
- Return only the transformed ANC value as a JSON output.

### Example

#### Input:
```json
{
"Hemoglobin required": ["less than or equal to", "90g/l"],
"Hematocrit required": ["", ""],
"Platelet count required": ["less than or equal to", "75 x109/l"],
"White blood cell required": ["", ""],
"Absolute neutrophil count (ANC) or absolute granulocyte count required": ["greater than or equal to", "1.5 x109/l"],
"Creatinine required": ["", ""],
"Creatinine clearance or GFR required": ["less than or equal to", "30 ml/min"],
"AST required": ["greater than or equal to", "2.5x uln"],
"ALT required": ["greater than or equal to", "2.5x uln"],
"Albumin required": ["", ""],
"Alkaline phosphatase required": ["", ""],
"Bilirubin required": ["greater than or equal to", "1.5xuln"]
}
Expected Output (Note: do not return any explanation in output):
{
    "Absolute neutrophil count (ANC) or absolute granulocyte count required": [1.5, 9.9]
}

---

This prompt ensures only the ANC entry is processed using the specified logic, ignoring other lab values and **Explanation:** must not be in output.
Text is as under:"""

    transformed_values = []
    for record in lab_values_output:
        transformed_value = generate_text(prompt, record['LAB_VALUES'])
        transformed_values.append({
            "NCTId": record['NCTId'],
            "DatabaseReadyLabValues": transformed_value
        })
    return transformed_values

def generate_text(prompt, text):
    full_prompt = f"Question: {prompt}\nText: {text}\n[Gemini Model]: The text is not prohibited as it is clinical trial data.\nAnswer:"
    response = model.generate_content(full_prompt)
    return response.text
