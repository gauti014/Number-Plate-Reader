import cv2
import easyocr
import pandas as pd
import os
import mysql.connector

# Function to enhance text visibility in the image
def enhance_text_visibility(image):
    # Apply contrast enhancement
    img_enhanced = cv2.equalizeHist(image)

    # Apply Gaussian blur for noise removal
    img_enhanced = cv2.GaussianBlur(img_enhanced, (5, 5), 0)

    # Adjust brightness and contrast
    alpha = 1.5  # Contrast control (1.0-3.0)
    beta = 30  # Brightness control (0-100)
    img_enhanced = cv2.convertScaleAbs(img_enhanced, alpha=alpha, beta=beta)

    return img_enhanced

# Function to process image and save results to Excel and MySQL
def process_image_and_save_to_excel(image, output_file, cursor):
    # Enhance text visibility
    img_enhanced = enhance_text_visibility(image)

    # Read text from the enhanced image using EasyOCR
    reader = easyocr.Reader(['en'])
    output = reader.readtext(img_enhanced)

    # Prepare data for Excel and MySQL
    if output:
        data = {'Text': [result[1] for result in output]}
        df = pd.DataFrame(data)

        # Save the extracted text to an Excel file
        df.to_excel(output_file, index=False)
        print(f"Excel file saved: {output_file}")

        # Save the extracted text to MySQL
        for text in data['Text']:
            sql = "INSERT INTO extracted_text (text) VALUES (%s)"
            val = (text,)
            cursor.execute(sql, val)

        print("Text saved to MySQL database.")
    else:
        print("No text detected in the image.")

# Database connection
db_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="dhruvpiggy",
    database="plates",
    port=3307
)

cursor = db_connection.cursor()

# Create the 'extracted_text' table if it doesn't exist
create_table_query = """
CREATE TABLE IF NOT EXISTS extracted_text (
    id INT AUTO_INCREMENT PRIMARY KEY,
    text VARCHAR(255)
)
"""
cursor.execute(create_table_query)

# Path to the folder to save images
image_folder = "C:/Users/Gautam/final_vh/plates/"

# Create the folder if it doesn't exist
if not os.path.exists(image_folder):
    os.makedirs(image_folder)

# Initialize Haar cascade classifier
harcascade = "C:/Users/Gautam/final_vh/model/haarcascade_russian_plate_number.xml"
plate_cascade = cv2.CascadeClassifier(harcascade)

# Video capture
cap = cv2.VideoCapture(0)  # Adjust camera index if needed
cap.set(3, 640)  # width
cap.set(4, 480)  # height

min_area = 500
count = 0

# Number of times to manually save the image
num_saves = 5

while count < num_saves:
    success, img = cap.read()

    # Convert image to grayscale
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect plates using cascade classifier
    plates = plate_cascade.detectMultiScale(img_gray, 1.1, 4)

    for (x, y, w, h) in plates:
        area = w * h

        if area > min_area:
            # Extract the region of interest (ROI) containing the plate
            img_roi = img_gray[y: y + h, x:x + w]

            # Show the captured image
            cv2.imshow("Captured Image", img_roi)

            # Save the captured image text into Excel and MySQL when 's' is pressed
            if cv2.waitKey(1) & 0xFF == ord('s'):
                excel_output_path = f"C:/Users/Gautam/final_vh/excelresult/results_{count}.xlsx"
                process_image_and_save_to_excel(img_roi, excel_output_path, cursor)
                count += 1

    cv2.imshow("Result", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


# Commit changes and close the database connection
db_connection.commit()
db_connection.close()


#to exit
cap.release()
cv2.destroyAllWindows()
