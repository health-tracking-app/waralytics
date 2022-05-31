# Intro
Collecting data from the [Oryx blog](https://www.oryxspioenkop.com/) on the equipment loss in the Ukraine-Russia war:
* Parsing webpage to create a dataset ([Ukraine](https://www.oryxspioenkop.com/2022/02/attack-on-europe-documenting-ukrainian.html) & [Russia](https://www.oryxspioenkop.com/2022/02/attack-on-europe-documenting-equipment.html))
* Recognizing dates of loss registration from the pictures (e.g. [like this](https://postlmg.cc/RN7tVvw5))
* If date is not recognized or source is Twitter get it's publishing date

# Results
Webpage parsing was pretty much straighforward, date recognition is a different thing. We were not sure how good it will be. It turned out pretty much good - about 90%. We randomly checked about 100 pictures - for all of them dates were correct. Moreover, 73% of dates were recognized from the 1st attempt (we are making 5 of them in total with different configs) - kudos to __@Shulitskyi__ for the idea of turning all non-black pixels into white before attempting text recognition.  Summary is in the below table (as of 2022-05-25).

| TYPE  | NUMBER | PERCENTAGE |
|-------|--------|------------|
| Picture | 4817   | 93,61%     |
| Tweet	| 329    | 6,39%      |
| **Total** | **5146**   | **100,00%** |

| PICTURE           | NUMBER | PERCENTAGE |
|-------------------|--------|------------|
| Image recognition | 4317   | 89,62%     |
| Metadata	         | 500    | 10,38%     |
| **Total**         | **4817**   | **100,00%** |

| IMAGE RECOGNITION | NUMBER   | PERCENTAGE |
|-------------------|----------|------------|
| Attempt 1         | 3157     | 73,13%    |
| Attempt 2 	     | 147      | 3,41%     |
| Attempt 3         | 732      | 16,96%     |
| Attempt 4         | 208      | 4,82%     |
| Attempt 5         | 73       | 1,69%     |
| **Total**         | **4317** | **100,00%** |

## External dependencies

### Chrome driver
Tool for loading web page with dynamically generated content.    
Works with requests-html Python library. Usually, library handles driver download itself.    
https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/

### Tesseract
Tool for recognizing text from images.    
Works with pytesseract Python library.    
Official repo (v3): https://tesseract-ocr.github.io/tessdoc/Downloads.html    
UB Mannheim (v3,4,5): https://github.com/UB-Mannheim/tesseract/wiki