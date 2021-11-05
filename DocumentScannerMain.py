import cv2
import numpy as np
import utlis
from skimage.filters import threshold_local
from pathlib import Path
from svgtrace import trace
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF, renderPM
import ocrmypdf
import PySimpleGUI as sg
import os
from PIL import Image
########################################################################

########################################################################

# variáveis
count = 0
loop = True
outcount = 0
# GUI

layout = [[sg.Combo(sorted(sg.user_settings_get_entry('-filenames-', [])), default_value=sg.user_settings_get_entry('-last filename-', ''), size=(50, 1), key='-FILENAME-'), sg.FolderBrowse(), sg.B('Clear History')],
          [sg.Button('Iniciar'),  sg.Button('Sair')]]

window = sg.Window('Digitalizador de documentos 0.3b', layout)

# Funcoes


def tratamento_potrace():
    THISDIR = str(Path(__file__).resolve().parent)
    bw = open(THISDIR + "/logo.svg", "w")
    bw.write(trace(THISDIR + "/myImage0.png", True))
    bw.close()


def svg_para_pdf():
    drawing = svg2rlg("logo.svg")
    renderPDF.drawToFile(drawing, "final2.pdf")


# Corpo do programa
while True:
    event, values = window.read()

    if event in (sg.WIN_CLOSED, 'Sair'):
        break
    if event == 'Iniciar':
        # If OK, then need to add the filename to the list of files and also set as the last used filename
        sg.user_settings_set_entry('-filenames-', list(set(sg.user_settings_get_entry('-filenames-', []) + [values['-FILENAME-'], ])))
        sg.user_settings_set_entry('-last filename-', values['-FILENAME-'])
        pathfiles = str(values.get('-FILENAME-'))
        for imagefiles in os.listdir(pathfiles):
            outcount += 1
            imagepath = os.path.join(pathfiles, imagefiles)
            img = cv2.imread(imagepath)

            # PREENCHE DE PRETO AO REDOR
            # row, col = imginput.shape[:2]
            # bottom = imginput[row - 2:row, 0:col]
            # mean = cv2.mean(bottom)[0]

            # bordersize = 40
            # img = cv2.copyMakeBorder(
            #     imginput,
            #     top=bordersize,
            #     bottom=bordersize,
            #     left=bordersize,
            #    right=bordersize,
            #    borderType=cv2.BORDER_CONSTANT,
            #    value=0
            # )
            cv2.imwrite(f'{pathfiles}/{imagefiles}_{outcount}_border.jpg', img)

            # TRATAMENTO PARA DETECTAR CONTORNOS
            heightImg = img.shape[0]
            widthImg = img.shape[1]
            img = cv2.resize(img, (widthImg, heightImg))   # ALTERAR TAMANHO
            imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # CONVERTE ESCALA DE CINZA
            imgBlur = cv2.GaussianBlur(imgGray, (5, 5), 0)  # ADICIONA GAUSS
            kernel = np.ones((5, 5))
            imgPrep1 = cv2.erode(imgBlur, kernel)  # ADICIONA DILATACAO
            imgPrep2 = cv2.morphologyEx(imgPrep1, cv2.MORPH_OPEN, kernel)
            imgPrep3 = cv2.morphologyEx(imgPrep2, cv2.MORPH_CLOSE, kernel)
            # imgThreshold = cv2.erode(imgDial, kernel, iterations=10)  # ADICIONA EROSAO
            # cv2.imwrite(f'{pathfiles}/{imagefiles}_{outcount}_thresh.jpg', imgThreshold)
            # Acha Contornos
            imgContours = img.copy()  # COPIA PARA DEBUG
            imgBigContour = img.copy()  # COPIA PARA DEBUG
            imgPrep4 = cv2.Canny(imgPrep3, 20, 240)  # ADICIONA Cannyi
            imgPrepFinal = cv2.dilate(imgPrep4, kernel)  # ADICIONA DILATACAO
            cv2.imwrite(f'{pathfiles}/{imagefiles}_{outcount}_erode.jpg', imgPrepFinal)
            contours, hierarchy = cv2.findContours(imgPrepFinal, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)  # ACHA TODOS
            cv2.drawContours(imgContours, contours, -1, (0, 255, 0), 10)  # DESENHA CONTORNOS
            cv2.imwrite(f'{pathfiles}/{imagefiles}_{outcount}_contour.jpg', imgContours)

            # ACHA O MAIOR CONTORNO
            biggest, maxArea = utlis.biggestContour(contours)  # FIND THE BIGGEST CONTOUR

            if biggest.size != 0:
                biggest = utlis.reorder(biggest)
                cv2.drawContours(imgBigContour, biggest, -1, (0, 255, 0), 20)  # DRAW THE BIGGEST CONTOUR
                imgBigContour = utlis.drawRectangle(imgBigContour, biggest, 2)
                cv2.imwrite("./MyImageBiggestContour" + str(count) + ".png", imgBigContour)
                pts1 = np.float32(biggest)  # PREPARAR PONTOS PARA MUDANÇA PERSPECTIVA
                pts2 = np.float32([[0, 0], [widthImg, 0], [0, heightImg], [widthImg, heightImg]])  # PREPARA OS SEGUNDOS PONTOS PARA MUDANÇA
                matrix = cv2.getPerspectiveTransform(pts1, pts2)
                print(biggest)
                print('----------------------------------------')
                print(pts1)
                imgWarpColored = cv2.warpPerspective(img, matrix, (widthImg, heightImg))

                #  REMOVER 20 PIXELS DOS LADOS
                imgWarpColored = imgWarpColored[20:imgWarpColored.shape[0] - 20, 20:imgWarpColored.shape[1] - 20]
                imgWarpColored = cv2.resize(imgWarpColored, (widthImg, heightImg))
            else:
                imgWarpColored = imgContours
            #  TRESHOLD ADAPTATIVO
            # imgWarpColored = cv2.cvtColor(imgWarpColored, cv2.COLOR_BGR2GRAY)
            # T = threshold_local(imgWarpColored, 11, offset=10, method="gaussian")
            # imgWarpColored = (imgWarpColored > T).astype("uint8") * 255

            # (thresh, blackAndWhiteImage) = cv2.threshold(imgWarpColored, 160, 255, cv2.THRESH_BINARY)
            cv2.imwrite(f'{pathfiles}/{imagefiles}_{outcount}.jpg', imgWarpColored)
            # if cv2.waitKey(1) & 0xFF == ord('s'):
            # cv2.imwrite("./myImage" + str(count) + ".png", imgWarpColored)
            # loop = False
            # tratamento_potrace()
            # svg_para_pdf()
            # if __name__ == '__main__':
            #     ocrmypdf.ocr('final2.pdf', 'finalizadofinal.pdf', language='eng', jobs='4', max_image_mpixels='90000000', deskew=False)
            # break

    elif event == 'Clear History':
        sg.user_settings_set_entry('-filenames-', [])
        sg.user_settings_set_entry('-last filename-', '')
        window['-FILENAME-'].update(values=[], value='')

window.close()
