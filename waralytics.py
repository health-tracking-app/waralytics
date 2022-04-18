import ssl
import requests
from urllib.request import urlretrieve
import re
from bs4 import BeautifulSoup
import pandas as pd
from PIL import Image
from pytesseract import pytesseract

import config


class WebParser:
    """
    Class to take a web page from Oryx blog and parse from it details about the arms losses.
    """

    def __init__(self, web_url: str):
        """
        :param web_url: URL from the Oryx website to parse
        """

        self.web_url = web_url

        # Web page's source code (unparsed)
        self.html_page = None
        # Web page's source code (parsed)
        self.html_soup = None
        # Dictionary with losses summary (from headings summaries)
        self.loss_sum_dict = None
        # List of all <ul> on the web page
        self.loss_det_raw = None
        # List of <ul> with information about the losses
        self.loss_det_filtered = None
        # Data frame with losses details (before expanding multiple losses rows into several lines)
        self.df_loss_raw = None
        # Data frame with losses details (one loss - one line)
        self.df_loss = None

        # On class initiation parse a web page
        self.parse_webpage()

    def parse_webpage(self):

        self.html_page = requests.get(self.web_url).content
        self.html_soup = BeautifulSoup(self.html_page, "html.parser")

    def extract_summary(self):

        # Losses summary are placed inside <h3>
        loss_sum_raw = self.html_soup.find_all('h3')

        # Data cleansing
        # TODO lets replace this with nice regex

        # Get rid of empty strings
        loss_sum = [i.text.strip() for i in loss_sum_raw if i.text.strip() != ""]
        # Get rod of unnecessary words/punctuation and standardize format
        loss_sum = [i.replace("of which:", "").replace("of which", "").replace(" And ", " and ") for i in loss_sum]
        loss_sum = [i.replace("Trucks, Vehicles and Jeeps", "Trucks and Vehicles and Jeeps") for i in loss_sum]
        loss_sum = [i.replace("(MRAP) ", "") for i in loss_sum]
        loss_sum = [i.replace(" - ", ":").replace("(", ":").replace(")", "") for i in loss_sum]
        # Convert list of strings into a list of dictionaries
        loss_sum_dict = [dict(i.split(":") for i in j.split(",")) for j in loss_sum]
        # Get rid of leading/trailing spaces in keys and values
        self.loss_sum_dict = [{a.strip(): b.strip() for a, b in i.items()} for i in loss_sum_dict]

    def extract_details(self):

        # Losses details are stored inside <ul>
        self.loss_det_raw = self.html_soup.find_all("ul")

        # Get rid of non-war losses details

        def det_filter(elm):
            pattern_1 = elm.next_element.name == "li" and elm.next_element.next_element.name == "img"
            pattern_2 = elm.next_element.name == "li" and elm.next_element.next_element.name == "span"
            result = pattern_1 or pattern_2
            return result

        self.loss_det_filtered = [i for i in self.loss_det_raw if det_filter(i)]

        # Construct a list with losses details

        # Supplementary functions

        def find_arm_producer(txt):
            txt = txt.lower()
            arm_prd = ""
            if "soviet" in txt and "union" in txt:
                arm_prd = "Soviet Union"
            elif "russia" in txt:
                arm_prd = "Russia"
            elif "belarus" in txt:
                arm_prd = "Belarus"
            elif "italy" in txt:
                arm_prd = "Italy"
            elif "czech" in txt and "republic" in txt:
                arm_prd = "Czech Republic"
            elif "israel" in txt:
                arm_prd = "Israel"
            elif "poland" in txt:
                arm_prd = "Poland"
            elif "ukraine" in txt:
                arm_prd = "Ukraine"
            elif ("united" in txt and "kingdom" in txt) or "britain" in txt:
                arm_prd = "United Kingdom"
            elif "united" in txt and "states" in txt:
                arm_prd = "United States"
            elif "turkey" in txt:
                arm_prd = "Turkey"
            return arm_prd

        def find_arm_owner(html_ul):

            # Default arm_category
            arm_own = ""

            # Generator to get all the previous siblings - more effective search
            gen_sib = html_ul.previous_siblings

            # Pattern for arm_owner
            # 'Russia - 2899, of which: destroyed: 1548, damaged: 44, abandoned: 237, captured: 1070'

            for sib in gen_sib:
                if sib.name == "h3" and "russia" in sib.text.lower() and "of which" in sib.text.lower():
                    arm_own = "Russia"
                    break
                elif sib.name == "h3" and "ukraine" in sib.text.lower() and "of which" in sib.text.lower():
                    arm_own = "Ukraine"
                    break

            if arm_own == "":

                # In some cases <h3> and <ul> are encircled in <div>
                # In that case <ul> has only one previous sibling - <h3> with arm_category
                # Therefore, to find arm_own we need to loop through all the previous elements
                # and not just siblings

                # Generator to get all the previous elements - less effective search
                gen_elm = html_ul.previous_elements

                for sib in gen_elm:
                    if sib.name == "h3" and "russia" in sib.text.lower() and "of which" in sib.text.lower():
                        arm_own = "Russia"
                        break
                    elif sib.name == "h3" and "ukraine" in sib.text.lower() and "of which" in sib.text.lower():
                        arm_own = "Ukraine"
                        break

            return arm_own

        def find_arm_category(html_li):

            # Default arm_category
            arm_ctg = ""

            # Generator to get all the previous siblings
            gen_sib = html_li.previous_siblings

            # Pattern for arm_category
            # 'Tanks (507, of which destroyed: 257, damaged: 9, abandoned: 40, captured: 201)'
            arm_ctg_pattern_1 = re.compile(r"^\w*.*\(\d*.*of which")
            arm_ctg_pattern_2 = re.compile(r"\(\d+.*of which")

            # We are doing search up to 4 levels back, otherwise something is wrong
            i = 4

            try:
                while i > 0:
                    sib = next(gen_sib)
                    if sib.name == "h3" and sib.text.strip() != "":
                        # 'Tanks (507, of which'
                        arm_ctg_txt = arm_ctg_pattern_1.search(sib.text.strip()).group()
                        # '(507, of which'
                        arm_ctg_pos = arm_ctg_pattern_2.search(arm_ctg_txt).start()
                        # "Tanks"
                        arm_ctg = arm_ctg_txt[:arm_ctg_pos].strip()
                        break
                    i -= 1
            except StopIteration:
                pass

            return arm_ctg

        # Loop through the list of losses and construct a list with irs details

        list_loss = []

        for elm_ul in self.loss_det_filtered:
            arm_owner = find_arm_owner(elm_ul)
            arm_category = find_arm_category(elm_ul)
            for elm_li in elm_ul:
                arm_producer = find_arm_producer(elm_li.img["src"])
                arm_model = elm_li.text.strip()[elm_li.text.strip().find(" ") + 1: elm_li.text.strip().find(":")]
                for elm_a in elm_li.find_all("a"):
                    arm_id_action = elm_a.text.strip(" ()")  # elm_a.text[elm_a.text.find(",") + 1:].strip(" )")
                    arm_photo_url = elm_a["href"].strip()
                    elm_list_loss = [arm_category, arm_model, arm_id_action, arm_photo_url, arm_producer, arm_owner]
                    list_loss.append(elm_list_loss)

        df_columns = ["Equipment Category", "Equipment Type", "Action Type", "Source Link", "Equipment Producer",
                      "Impacted Country"]

        self.df_loss_raw = pd.DataFrame(data=list_loss, columns=df_columns)

        # Initialize Tesseract image recognizer
        # tsr = ImageRecognizer(config.path_tsr)

        # Recognize all the text from the image
        # self.df_loss_raw = self.df_loss_raw[1:10]

        # self.df_loss_raw["Recognized text from image"] = self.df_loss_raw.apply(lambda x: tsr.parse_txt_from_img(x["Source Link"]), axis=1)


class ImageRecognizer:
    """
    Class to take an image and recognize all the text on it.
    """


    def __init__(self, path_tsr: str):
            """
            :param path_tsr: Path to Tesseract engine .exe
            """

            self.path_tsr = path_tsr

            # Avoid website certificate validation errors
            ssl._create_default_https_context = ssl._create_unverified_context

            # Point pytesseract to the Tesseract engine's .exe
            pytesseract.tesseract_cmd = self.path_tsr

    def parse_txt_from_img(self, img_url):
        """
        Parse a web image to retrieve all the text from it.
        """

        # Download the image
        try:
            urlretrieve(img_url, "file_img")
        except Exception as e:
            err_msg = repr(e)
            return err_msg

        # Open the image
        try:
            img = Image.open("file_img")
        except Exception as e:
            err_msg = repr(e)
            return err_msg

        # Recognize text from the image
        # Tesseract has a different modes of text recognitions
        # The ones worked the best for us are:
        #   - 6 => Assume a single uniform block of text
        #   - 11 => Sparse text. Find as much text as possible in no particular order
        #   - 12 => Sparse text with OSD
        img_txt = pytesseract.image_to_string(img, config='--psm 11')

        # Get rid of white spaces
        p = re.compile(r"\s+")
        img_txt = re.sub(p, '', img_txt)

        return img_txt
