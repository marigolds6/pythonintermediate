import rasterio
with rasterio.open(u'C:\\grb\\Test.grb') as source:
    band = source.read_band(1)
meta = source.meta
meta.update(driver=u'GTiff', dtype=rasterio.uint8)
with rasterio.open(u'C:\\grb\\output2.tif','w',**meta) as sink:
	sink.write_band(1,band.astype(rasterio.uint8))
