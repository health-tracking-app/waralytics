import os
from time import time
import pandas as pd

import waralytics
import config


def timer_func(func):
    """
    Decorator that shows execution time of a function.
    """
    def wrap_func(*args, **kwargs):
        t1 = time()
        result = func(*args, **kwargs)
        t2 = time()
        print(f'Function {func.__name__!r} executed in {(t2-t1):.4f}s')
        return result
    return wrap_func


@timer_func
def generate_report(url_to_parse, path_tsr, recon=True, db_username=None, db_password=None,
                    db_host=None, db_port=None, db_name=None):

    # Initialize web parser
    web_parser = waralytics.WebParser(url_to_parse)

    # Initialize Tesseract image recognizer
    tsr = waralytics.ImageRecognizer(path_tsr)

    # Initialize date parser
    date_parser = waralytics.DateParser()

    # Extract details about equipment losses from the webpage
    web_parser.extract_details()

    # If we are running reconciliation, extract old info from the db and update there ref data tables
    if recon:
        # Check if all the required arguments are present
        check_recon_args = [db_username, db_password, db_host, db_port, db_name]
        if not all(check_recon_args):
            return "Please provide db_username, db_password, db_host, db_port, db_name to connect to a database"
        # Initialize data reconciliation
        data_recon = waralytics.DataReconciliation(db_username, db_password, db_host, db_port, db_name)
        # Reconcile new (parsed from the webpage) and old (extracted from the database) data
        # Update ref data table in the database
        data_recon.update_db_step_1(web_parser.df_loss_raw)

    # Define df we will be working with
    if recon:
        df_work = data_recon.reconciled_df
    else:
        df_work = web_parser.df_loss_raw

    # Get a list of unique source links
    src_links = list(set(list(df_work["Source Link Final"])))

    # Split links between pictures' bank (to parse date from the image) and twitter
    # (to parse date from the webpage)
    src_link_pictures = [i for i in src_links if "twitter" not in i]
    src_link_twitter = [i for i in src_links if "twitter" in i]

    # Create a list to store text recognized from images and webpages
    rec_dates = []

    # Recognize dates from images
    counter = 1
    for link in src_link_pictures[1:2]:
        # We will make several recognition attempts with different configurations
        # Attempt 1
        print(f"Pic {counter}: attempt 1")
        img_txt = tsr.parse_txt_from_img(link, black_white=True)
        date_txt = date_parser.parse_date_from_txt(img_txt, "pic")
        if not date_txt:
            # Attempt 2
            print(f"Pic {counter}: attempt 2")
            # In case date overlay is in white color
            img_txt = tsr.parse_txt_from_img(link, invert_img=True, black_white=True)
            date_txt = date_parser.parse_date_from_txt(img_txt, "pic")
        if not date_txt:
            # Attempt 3
            print(f"Pic {counter}: attempt 3")
            img_txt = tsr.parse_txt_from_img(link)
            date_txt = date_parser.parse_date_from_txt(img_txt, "pic")
        if not date_txt:
            # Attempt 4
            print(f"Pic {counter}: attempt 4")
            img_txt = tsr.parse_txt_from_img(link, adjust_img=True)
            date_txt = date_parser.parse_date_from_txt(img_txt, "pic")
        if not date_txt:
            # Attempt 5
            print(f"Pic {counter}: attempt 5")
            img_txt = tsr.parse_txt_from_img(link, adjust_img=True, invert_img=True)
            date_txt = date_parser.parse_date_from_txt(img_txt, "pic")
        elm_rec_txt = [link, img_txt, date_txt]
        rec_dates.append(elm_rec_txt)
        counter += 1

    # Recognize text from webpages
    counter = 1
    for link in src_link_twitter[1:2]:
        # We will make a several attempts with different sleep timeouts to find a balance between speed
        # and effectiveness.
        # Attempt 1
        print(f"Tweet {counter}: attempt 1")
        twit_parser = waralytics.WebParser(link, js_content=True, sleep=3)
        twit_txt = twit_parser.extract_date_txt_from_twit()
        date_txt = date_parser.parse_date_from_txt(twit_txt, "twit")
        if not date_txt:
            # Attempt 2
            print(f"Tweet {counter}: attempt 2")
            twit_parser = waralytics.WebParser(link, js_content=True, sleep=5)
            twit_txt = twit_parser.extract_date_txt_from_twit()
            date_txt = date_parser.parse_date_from_txt(twit_txt, "twit")
        if not date_txt:
            # Attempt 3
            print(f"Tweet {counter}: attempt 3")
            twit_parser = waralytics.WebParser(link, js_content=True, sleep=10)
            twit_txt = twit_parser.extract_date_txt_from_twit()
            date_txt = date_parser.parse_date_from_txt(twit_txt, "twit")
        elm_rec_txt = [link, twit_txt, date_txt]
        rec_dates.append(elm_rec_txt)
        counter += 1

    # Convert list to a data frame
    rec_dates_df = pd.DataFrame(data=rec_dates, columns=["Source Link Final", "Recognized Text", "Event Date"])

    # Merge main data frame with the one with event dates
    df_work = df_work.merge(rec_dates_df, how='outer', on='Source Link Final')

    # Replicate rows, which contain info about several hit objects
    df_final = web_parser.replicate_lines(df_work)

    # Update db
    if recon:
        data_recon.update_db_step_2(df_final)

    return df_final


# GENERATE REPORTS W/O DOING RECONCILIATION

# Generate reports
war_loss_ua = generate_report(config.url_ua_loss, config.path_tsr, recon=False)
war_loss_ru = generate_report(config.url_ru_loss, config.path_tsr, recon=False)

# Save reports
war_loss_ua.to_csv("war_loss_ua.csv", sep=";")
war_loss_ru.to_csv("war_loss_ru.csv", sep=";")

# GENERATE REPORTS W/ DOING RECONCILIATION AND UPDATING TABLES ON DB

# Import parameters required to connect to a database
# db_username = os.environ["DB_USERNAME"]
# db_password = os.environ["DB_PASSWORD"]
# db_host = os.environ["DB_HOST"]
# db_port = os.environ["DB_PORT"]
# db_name = os.environ["DB_NAME"]
#
# # Generate reports and update logs table of the database
# war_loss_ua = generate_report(config.url_ua_loss, config.path_tsr, db_username=db_username, db_password=db_password,
#                               db_host=db_host, db_port=db_port, db_name=db_name)
# war_loss_ru = generate_report(config.url_ru_loss, config.path_tsr, db_username=db_username, db_password=db_password,
#                               db_host=db_host, db_port=db_port, db_name=db_name)
#
# # Save reports
# war_loss_ua.to_csv("war_loss_ua.csv", sep=";")
# war_loss_ru.to_csv("war_loss_ru.csv", sep=";")