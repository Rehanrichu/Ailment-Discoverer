print("--- ⚖️ BODY MASS INDEX CALCULATOR ⚖️ ---")

weight = float(input("Enter weight (kg): "))
height = float(input("Enter height (meters): "))
heights = height*height

bmi = round(weight / heights,3)

print("Your Body MASS INDEX will be",bmi,"kg/m^2")

if bmi < 18.5:
    status = " an Underweight - Suggesting Protein-rich Diet"
elif 18.5 <= bmi <= 24.9:
    status = " a Healthy Weight - Maintain Current Activity"
elif 25 <= bmi <= 29.9:
    status = " an Overweight - Suggesting Cardiovascular Exercise"
else:
    status = " an Obese - Clinical Consultation Recommended"

print("You have",status)
