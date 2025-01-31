import cv2
import numpy as np
import pandas as pd
import os
from app import app as APP
import re
import pytesseract as tess

#Set the location of Tesseract

#This is for windows
#tess.pytesseract.tesseract_cmd = os.path.join(os.path.dirname(APP.config['APP_PATH']),r'Tesseract-OCR/tesseract.exe')
#This is for linux
tess.pytesseract.tesseract_cmd = '/usr/bin/tesseract'



class ExtractData:
    #Start the initial variables
    def __init__(self, img_path):
        self.img_path = img_path
        
        #Store text found by tesseract
        self.doc_text = ''
        #Store the text as a dicc
        self.text_struct = ''

        #Due to the fied 'Domicilio' there may be a different lenght of rows, we use 'Clave Elector' as reference
        self.indx_clv_elec = -1

        self.send_data = []
        self.perc_found = 0

        self.graph_data = {}

        # This is the data that we are looking for
        self.data_f = {
                'nombre': '',
                'domicilio': '',
                'clave_elector': '',
                'curp': '',
                'registro': '',
                'estado': '',
                'municipio': '',
                'seccion': '',
                'localidad': '',
                'emision': '',
                'vigencia': '',
                'nacimiento': '',
                'sexo': ''
            }

    def extract_text_from_image(self, croppe=False):
        # Load the image using OpenCV
        image = cv2.imread(self.img_path)

        # In this section we wanna focus where the data is.
        if croppe:
            # Resize the image for better accuracy (optional)
            
            # Convert the image to grayscale
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Apply a median blur to reduce noise
            gray_image = cv2.medianBlur(gray_image, 3)
            
            # Apply adaptive thresholding
            adaptive_thresh = cv2.adaptiveThreshold(
                gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 91, 2)
            
            
            # Apply morphological operations to close gaps and reduce noise
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            morph_image = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)
            
            # Apply Canny edge detection
            edges = cv2.Canny(morph_image, 50, 150)
            
            # Find contours on the edged image
            contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            # Initialize a variable to store the largest rectangle contour
            largest_rect = None
            largest_area = 0
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < 1000:  # Filter out small contours by area
                    continue

                # Approximate the contour to a polygon
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Check if the approximated contour has four points (rectangle)
                if len(approx) == 4:
                    if area > largest_area:
                        largest_area = area
                        largest_rect = approx
            
            """# Draw all contours for visualization
            contour_image = image.copy()
            cv2.drawContours(contour_image, contours, -1, (0, 255, 0), 2)  # Draw all contours in green
            
            # Draw all rectangular contours
            for contour in contours:
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                if len(approx) == 4:
                    cv2.drawContours(contour_image, [approx], -1, (255, 0, 0), 2)  # Draw all rectangles in blue
            
            # Draw the largest rectangle contour in red
            if largest_rect is not None:
                cv2.drawContours(contour_image, [largest_rect], -1, (0, 0, 255), 2)  # Draw the largest rectangle in red"""


            # If a rectangle was found then crop the image in that rectangle size
            if largest_rect is not None:
                x, y, w, h = cv2.boundingRect(largest_rect)
                final_img_use = image[y:y+h, x:x+w]
            else:
                final_img_use = image
        else:
            #If we are not going to crop the image then we just use the original
            final_img_use = image


        cropped_image_re = cv2.resize(final_img_use, (0, 0), fx=1.8, fy=1.8)
        
        # Convert the cropped image to grayscale
        gray_cropped = cv2.cvtColor(cropped_image_re, cv2.COLOR_BGR2GRAY)
        
        # Apply a median blur to reduce noise
        gray_cropped = cv2.medianBlur(gray_cropped, 1)

        # Apply binary thresholding
        _, binary_image = cv2.threshold(gray_cropped, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Use Tesseract to extract text
        text = tess.image_to_string(binary_image)
        
        #Finally store the text
        self.doc_text = text
        
        return True

    def structure_data(self):
        #We structure the data found in the image to have better manipulation.
        lines = self.doc_text.split('\n')
        data = {}
        count = 0
        for i in range(len(lines)):

            if lines[i] != '' and len(lines[i]) >= 3:
                data[count] = lines[i]
                count += 1

        self.text_struct = data

        return True

    #Find Data   
    def num_from_str(self, string):
        # Find all numeric sequences in the text
        numbers = re.findall(r'\d+', string)
        
        # Join all numbers into a single string
        concatenated_number = ''.join(numbers)
        
        return concatenated_number

    def extract_NOMBRE_NACIM_SEX(self):
        #We stablish the pattern of the data we are looking for
        pattern = re.compile(r'\b\w*NOMBRE\w*\b', re.IGNORECASE)

        #Then we itarete through the structured text.
        for key, line in self.text_struct.items():

            match = pattern.search(line)
            # Check if the pattern matched
            if match:

                try:

                    line_data_1 = self.text_struct[key+1].split(' ')
                    last_name_1 = line_data_1[0]

                    #The birth date is in the same line as the first last name
                    self.data_f['nacimiento'] = line_data_1[1]

                    line_data_2 = self.text_struct[key + 2].split(' ')
                    last_name_2 = line_data_2[0]

                    #The sex is in the same line as the second last name
                    if len(line_data_2) >= 3:
                        
                        self.data_f['sexo'] = line_data_2[2]
                    
                    raw_name = self.text_struct[key + 3].split(' ')

                    filter_name = [part for part in raw_name if len(part) > 1]
            
                    # Join the filtered words into a single string
                    name = ' '.join(filter_name)
                    
                    self.data_f['nombre'] = f'{name} {last_name_1} {last_name_2}'
                    return True
                except:
                    return False

    def extract_DOMICILIO(self):

        pattern = re.compile(r'\bDOMIC\w*\b', re.IGNORECASE)

        for key, value in self.text_struct.items():
            if pattern.search(value):

                indx_domici = key
                direc = ''
                for key_2, value in self.text_struct.items():
                    if indx_domici < key_2 < self.indx_clv_elec:
                        direc += ' ' + value

                self.data_f['domicilio'] = direc
                return True
            
        return False
    
    def extract_CLAVE_DE_ELECTOR(self):

        pattern = re.compile(r'\bCLAVE\s+DE\s+ELECTOR\s+(\S+)', re.IGNORECASE)

        for key, line in self.text_struct.items():

            match = pattern.search(line)

            if match:
                try:
                    extracted_value = match.group(1)  # Get the first capturing group
                    self.data_f['clave_elector'] = extracted_value
                except:
                    pass
                self.indx_clv_elec = key
                return True
            
        return False
    
    def extract_EDO_MUNP_SECC(self):

        # Pattern to match any word containing 'ESTADO'
        pattern_edo = re.compile(r'\b\w*ESTA\w*\b', re.IGNORECASE)

        # Iterate over the lines in self.text_struct
        for key, line in self.text_struct.items():
            
            # Search for the pattern in the line
            match = pattern_edo.search(line)
            
            # Print if a match was found
            if match:
                line_values = line.split(' ')
                try:
                    self.data_f['estado'] = self.num_from_str(line_values[1])
                except:
                    pass
                try:
                    self.data_f['municipio'] = self.num_from_str(line_values[3])
                except:
                    pass
                try:
                    self.data_f['seccion'] = self.num_from_str(line_values[5])
                except:
                    pass

    def extract_CURP_REGIS(self):

        pattern = re.compile(r'\b\w*CUR\w*\b', re.IGNORECASE)

        for key, line in self.text_struct.items():

            match = pattern.search(line)

            if match:
                line_data = self.text_struct[key].split(' ')
                try:
                    self.data_f['curp'] = line_data[1]
                except:
                    pass
                try:
                    self.data_f['registro'] = line_data[-2]
                except:
                    pass

                return True
    
        return False

    def extract_LOC_EMIS_VIGEN(self):

        pattern =  re.compile(r'\b\w*(?:LOCALIDAD|EMISION|VIGENCIA)\w*\b', re.IGNORECASE)

        for key, line in self.text_struct.items():
            
            # Search for the pattern in the line
            match = pattern.findall(line)
            if match:
                line_values = line.split(' ')
                try:
                    self.data_f['localidad'] =self.num_from_str(line_values[1])
                except:
                    pass                    
                try:
                    self.data_f['emision'] = self.num_from_str(line_values[3])
                except:
                    pass
                try:
                    self.data_f['vigencia'] = self.num_from_str(line_values[5])
                except:
                    pass
                return True
            
        return False
    
    def sinte(self):
        data = []
        count_found = 0
        indx = 0
        for key, value in self.data_f.items():

            found = value != ''

            item = {
                'id': indx,
                'key': key,
                'value': value,
                'found': found
            }

            data.append(item)

            #Increment values found
            if found:
                count_found +=1

            #Increment index value
            indx +=1

        if count_found !=0:
            #Calculate the percentage of data found
            self.perc_found = np.round((count_found/len(self.data_f))*100)
        
        self.send_data = data

        return True

    def calculate_perce(self):
        perc_local = self.perc_found

        graph = {
            'values': [perc_local,100-perc_local],
            'lables': ['',''],
            'colors': ['#FDFEFE','#FDFEFE'],
            'percentage': perc_local
        }
        #Give a color to the graph according to the percentage
        if perc_local >= 95:
            graph['colors'][0] = '#2ECC71'

        elif perc_local >= 75:
            graph['colors'][0] = '#F4D03F'

        elif perc_local >= 50:
            graph['colors'][0] = '#F39C12'
        else:
            graph['colors'][0] = '#E74C3C'

        self.graph_data = graph

        return True

    def start_finding(self):
        # Just go through each method to find the data
        self.extract_NOMBRE_NACIM_SEX()
        self.extract_CLAVE_DE_ELECTOR()
        if self.indx_clv_elec != -1:
            self.extract_DOMICILIO()
        self.extract_EDO_MUNP_SECC()
        self.extract_CURP_REGIS()
        self.extract_LOC_EMIS_VIGEN()

    def execute(self):

        self.extract_text_from_image(croppe=True)
        self.structure_data()
        #It`s possible that the cropped part went wrong due to different sizing, so if we don't find enough data we are going to repeat the process but without cropping.
        if len(self.text_struct) <= 5:
            self.extract_text_from_image()
            self.structure_data()
            
        #Now that we have the data we start looking for the fields.
        self.start_finding()

        self.sinte()
        self.calculate_perce()