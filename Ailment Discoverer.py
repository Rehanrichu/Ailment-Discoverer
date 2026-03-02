# Ailment Discoverer : Demo version
# Developed by: Muhammed Rehan C.K.

print("--- 🏥 AILMENT DISCOVERER: AI RESEARCH PROTOTYPE 🏥 ---")
print("Answer 'yes' or 'no' to the following symptoms:\n")

# --- SYMPTOMS ONE BY ONE ---
high_fever = input("Do you have a sustained high fever (39-40°C)? ").lower()
stomach_pain = input("Do you have severe stomach pain? ").lower()
constipation = input("Are you experiencing constipation? ").lower()
headache = input("Do you have a frequent headache? ").lower()
loss_of_appetite = input("Have you lost your appetite? ").lower()
cough = input("Do you have a persistent cough? ").lower()
chills = input("Do you feel chills or shivering? ").lower()
blue_nails = input("Are your lips or fingernails turning gray/blue? ").lower()
nasal_congestion = input("Do you have a blocked/runny nose or sore throat? ").lower()
fatigue = input("Do you feel fatigue or tiredness all day? ").lower()
cyclic_fever = input("Does your fever come and go every 3 to 4 days? ").lower()
mucous_stool = input("Is there excess mucous or blood in your stool? ").lower()
internal_bleeding = input("Are there signs of internal bleeding or anemia? ").lower()
muscular_pain = input("Do you have aching muscular pain? ").lower()
itchy_skin = input("Do you have dry, scaly lesions or intense itching on skin? ").lower()

print("\n--- 📋 DIAGNOSIS REPORT ---")


# 1. Typhoid 
if high_fever == "yes" and stomach_pain == "yes" and headache == "yes" and constipation == "yes":
    print("📍 Possible Match: Typhoid (Salmonella typhi)")
    print("What is it: A bacterial infection spread through contaminated food/water.")
    print("NCERT Note: Usually includes sustained high fever and intestinal blockage in severe cases.")

# 2. Pneumonia 
if cough == "yes" and chills == "yes" and headache == "yes" and high_fever == "yes":
    print("📍 Possible Match: Pneumonia (Streptococcus pneumoniae)")
    print("What is it: An infection that inflames the air sacs in the lungs.")
    if blue_nails == "yes":
        print("🚨 CRITICAL: Gray/Blue nails indicate severe oxygen drop. EMERGENCY!")

# 3. Common Cold
if nasal_congestion == "yes" and sore_throat == "yes" and cough == "yes" and high_fever != "yes":
    print("📍 Possible Match: Common Cold (Rhino viruses)")
    print("What is it: A viral infection of the upper respiratory tract.")
    print("NCERT Note: It affects the nose and throat, but NOT the lungs.")

# 4. Malaria
if cyclic_fever == "yes" and chills == "yes" and fatigue == "yes":
    print("📍 Possible Match: Malaria (Plasmodium vivax)")
    print("What is it: A disease caused by a parasite transmitted by Anopheles mosquitoes.")
    print("NCERT Note: Chills and high fever recur every 3 to 4 days.")

# 5. Amoebiasis
if mucous_stool == "yes" and stomach_pain == "yes" and constipation == "yes":
    print("📍 Possible Match: Amoebiasis (Entamoeba histolytica)")
    print("What is it: An intestinal infection caused by an amoeba.")
    print("NCERT Note: Stools often contain excess mucous and blood clots.")

# 6. Ascariasis
if internal_bleeding == "yes" and muscular_pain == "yes" and high_fever == "yes":
    print("📍 Possible Match: Ascariasis (Ascaris lumbricoides)")
    print("What is it: An infection caused by the common roundworm.")
    print("NCERT Note: It can cause blockage of the intestinal passage.")

# 7. Ringworms
if itchy_skin == "yes":
    print("📍 Possible Match: Ringworms (Microsporum/Trichophyton)")
    print("What is it: A fungal infection that causes dry, scaly skin lesions.")
    

print("\n---------------------------------------------------------")
print("⚠️ MEDICAL DISCLAIMER:")
print("This is an AI Research Prototype. The diagnosis can be TRUE or FALSE.")
print("PLEASE GO AND CONSULT A DOCTOR (GP) FOR PROFESSIONAL ADVICE.")
print("---------------------------------------------------------")
