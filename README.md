# waralytics
Dashboard that shows information about the equipment losses of countries during military conflicts.

# Workspace set-up

## Create virtuals environment
python -m venv .venv

## Activate virtuals environment
.venv/Scripts/activate

## Install dependencies
pip install -r requirements.txt

## External dependencies

### ExifTool
Tool for reading metadata from pictures.
Works with PyExifTool Python library.
https://exiftool.org/install.html

### Chrome Driver
Tool for loading web page with dynamically generated content.
Works with requests-html Python library. Usually, library handles driver download itself.
https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/

### Tesseract
Tool for recognizing text from images.
Works with pytesseract Python library.
Official repo (v3): https://tesseract-ocr.github.io/tessdoc/Downloads.html
UB Mannheim (v3,4,5): https://github.com/UB-Mannheim/tesseract/wiki

# Package usage
import warlytics  
a = waralytics.WebParser(config.url_ua_ru_loss)  
a.extract_details()  
a.df_loss_raw.to_csv("war_loss.csv")  
