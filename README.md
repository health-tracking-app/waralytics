# waralytics
Dashboard that shows information about the equipment losses of countries during military conflicts.

# Workspace set-up

## Create virtuals environment
python -m venv .venv

## Activate virtuals environment
.venv/Scripts/activate

## Install dependencies
pip install -r requirements.txt

# Package usage
import warlytics  
a = waralytics.WebParser(config.url_ua_ru_loss)  
a.extract_details()  
a.df_loss_raw.to_csv("war_loss.csv")  
