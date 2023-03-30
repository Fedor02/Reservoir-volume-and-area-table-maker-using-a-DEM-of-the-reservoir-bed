from osgeo import gdal
import numpy as np
import pandas as pd

#inputting parameters
min_elev = float(input("Введите минимальную высоту дна водохранилища по БС, м: "))
max_elev = float(input("Введите максимальную целевую высоту по БС, м: "))
levels = [float(value) for value in input("Введите дополнительные уровни водохранилища (через пробел), которые вы хотите включить в таблицу, м по БС: ").split()]
resX = float(input("Введите разрешение ЦМР по X, м: "))
resY = float(input("Введите разрешение ЦМР по Y, м: "))
area = resX*resY
elev = max_elev
step = float(input("Введите шаг уровня водохранилища, м: "))
n = int((max_elev-min_elev)/step + 1)

start_time = time.time()
#opening raster dataset
ds = gdal.Open("./DEM.tif")
band = ds.GetRasterBand(1)
dem = band.ReadAsArray()
no_data = band.GetNoDataValue()

#making 1-dimension massive
dem = dem[dem != no_data]

#making a list of levels
lt = []
for i in range(n):
    elev = min_elev + i*step
    lt.append(elev)
lt = lt + levels
lt = sorted(lt)

#making Columns
table = pd.DataFrame(columns = ["Уровень по БС", "Объём, км3", "Площадь, км2"])

#making Rows
for i in range(n + len(levels)):
    elev = lt[i]

    # calculating Volume in cubic kilometres
    dem_new = dem[dem < elev]
    dem_sum = (np.sum(elev - dem_new) * area)/1000000000

    # calculating Area in square kilometres
    k = len(dem_new)
    S = k*area/1000000

    #filling and adding row to previous iterations
    new_row = pd.Series({'Уровень по БС': elev,'Объём, км3': dem_sum,'Площадь, км2': S})
    new_table = pd.concat([table, new_row.to_frame().T], ignore_index=True)
    table = new_table

# exporting to .xlsx format table
table.to_excel("result.xlsx")