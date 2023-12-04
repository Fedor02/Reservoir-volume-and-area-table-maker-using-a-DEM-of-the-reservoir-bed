from osgeo import gdal, ogr
import numpy as np
import pandas as pd
import os

min_elev = float(input("Введите минимальную целевую высоту по БС, м: "))
max_elev = float(input("Введите максимальную целевую высоту по БС, м: "))
levels = [float(value) for value in input("Введите дополнительные уровни водохранилища (через пробел), которые вы хотите включить в таблицу, м по БС: ").split()]
resX = float(input("Введите разрешение ЦМР по X, м: "))
resY = float(input("Введите разрешение ЦМР по Y, м: "))
area = resX*resY
elev = max_elev
step = float(input("Введите шаг уровня в таблице, м: "))
n = int((max_elev-min_elev)/step + 1)

# opening raster dataset
ds = gdal.Open("./DEM.tif")
band = ds.GetRasterBand(1)
dem = band.ReadAsArray()
rshape = dem.shape
rwth = rshape[1]
rhgt = rshape[0]
no_data = band.GetNoDataValue()

# making a list of levels
lt = []
for i in range(n):
    elev = min_elev + i*step
    lt.append(elev)
lt = lt + levels
lt = sorted(lt)

# opening vector dataset and getting layer
vec = ogr.Open("./Vector.shp")
layer = vec.GetLayer()

#rasterizing vector layer
opts = gdal.RasterizeOptions(format = "GTiff", outputType = gdal.GDT_Byte,
                             width = rwth, height = rhgt, xRes = resX, yRes = resY,
                             attribute = "Number", noData = 0)

raster_vec = gdal.Rasterize("./Raster_vec.tiff",
                            "./Vector.shp", options=opts)

# reading mask array
band_ras_vec = raster_vec.GetRasterBand(1)
mask_ras_vec = band_ras_vec.ReadAsArray()

# making logical filter
flt = np.logical_and(mask_ras_vec != 0, dem != no_data)

# making 1-dimension massives by filter
mask_ras_vec = mask_ras_vec[flt]
dem_flt = dem[flt]

# working with each object in vector layer
for feature in layer:

    # Getting feature Name and Number
    fieldName = feature.GetField("Name")
    fieldNumber = feature.GetField("FID")
    dem_mask = dem_flt[np.where(mask_ras_vec == fieldNumber)]

    # making Columns
    table = pd.DataFrame(columns = ["Уровень по БС", "Объём, км3", "Площадь, км2", "Часть водохранилища"])

    # making Rows
    for i in range(n + len(levels)):
        elev = lt[i]

        # calculating Volume in cubic kilometres
        dem_new = dem_mask[np.where(dem_mask < elev)]
        dem_sum = (np.sum(elev - dem_new) * area) / 1000000000

        # calculating Area in square kilometres
        k = len(dem_new)
        S = k*area/1000000

        # filling and adding row to previous iterations
        new_row = pd.Series({'Уровень по БС': elev,'Объём, км3': dem_sum ,'Площадь, км2': S, 'Часть водохранилища': feature.GetField("Name")})
        new_table = pd.concat([table, new_row.to_frame().T], ignore_index=True)
        table = new_table

    # exporting to .xlsx format table for each object in vector layer
    output_name = f"{fieldName}.xlsx"
    table.to_excel(output_name)

# deleting raster dataset
del raster_vec
os.unlink("./Raster_vec.tiff")

