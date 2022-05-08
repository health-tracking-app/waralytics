import pandas as pd

import waralytics
import config


def generate_report(url_to_parse, path_tsr):

    # Initialize web parser
    web_parser = waralytics.WebParser(url_to_parse)

    # Initialize Tesseract image recognizer
    tsr = waralytics.ImageRecognizer(path_tsr)

    # Initialize date parser
    date_parser = waralytics.DateParser()

    # Extract details about equipment losses from the webpage
    web_parser.extract_details()

    # Get a list of unique source links
    src_links = list(set(list(web_parser.df_loss_raw["Source Link Final"])))

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

    # Merge main data frame with the ones with event dates
    web_parser.df_loss_raw = web_parser.df_loss_raw.merge(rec_dates_df, how='outer', on='Source Link Final')

    # Replicate rows, which contain info about several hit objects
    web_parser.replicate_lines()

    return web_parser.df_loss_final


# Generate reports
war_loss_ua = generate_report(config.url_ua_loss, config.path_tsr)
war_loss_ru = generate_report(config.url_ru_loss, config.path_tsr)

# Save reports
war_loss_ua.to_csv("war_loss_ua.csv", sep=";")
war_loss_ru.to_csv("war_loss_ru.csv", sep=";")
