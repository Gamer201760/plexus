## Annual lights at night stack at 500 m
## tom.hengl@opengeohub.org
## https://doi.org/10.5281/zenodo.7750174

library(terra)
## terra 1.8.63
library(parallel)

in.tifs = list.files(pattern=glob2rx("VNL_*.average_masked*.tif"), full.names = TRUE, recursive = TRUE)
years.lst = 2000:2011
## year 2012 is not trust-worthy for modeling?
#sel.tifs = in.tifs[-grep("201204-201212", in.tifs)]
in.years = 2012:2024
sel.tifs = in.tifs[c(3:13,1:2)]
## prepare directories
tile.tbl = vect("global_tiling_system_500km.gpkg")
## 1046 dirs
#new.dirs <- paste0("./tiles/T", tile.tbl$ID)
#x <- lapply(new.dirs, dir.create, recursive=TRUE, showWarnings=FALSE)

## Run extrapolation in parallel per tile:
tif.r = rast(sel.tifs)
max.x = 2000
cl <- makeCluster(detectCores())
clusterExport(cl, c("in.years", "years.lst", "max.x"))
#j = which(tile.tbl$ID=="1429")
#j = which(tile.tbl$ID=="1500") ## Beijing
for(j in sample(1:length(tile.tbl$ID))){
  out.tifs = paste0("./tiles/T", tile.tbl$ID[j], "/nightlights.", years.lst, ".tif")
  if(any(!file.exists(out.tifs))){
    xs = terra::crop(tif.r, ext(tile.tbl[j]))
    xs = as.data.frame(xs, xy=TRUE, na.rm=FALSE)
    ## for logit-transformation add adjustment
    sd.x = parallel::parApply(cl, xs[,-c(1,2)]/max.x, 1, sd, na.rm=TRUE)<(8/2000)
    ## mask out all pixels with negative trend
    sd.N = parallel::parApply(cl, xs[,-c(1,2)]/max.x, 1, function(i){sum(diff(i))})< -(8/2000)
    #View(t(xs[177621,]))
    sd.df = which(!sd.x & !sd.N)
    sd.dr = which(sd.x & sd.N)
    if(length(sd.df)>0){
      t1s = data.frame(t(parallel::parApply(cl, xs[sd.df,-c(1,2)]/max.x, 1, function(i) { try( round( boot::inv.logit( predict(lm(y~x, data.frame(x=in.years, y=boot::logit(ifelse(as.vector(i)<=0, 0.001, ifelse(as.vector(i)>=1, 0.999, as.vector(i)))))), data.frame(x=years.lst)))*max.x ) ) })))
      #xp = data.frame(matrix(0, nrow=nrow(xs), ncol=ncol(t1s)))
      ## copy first year (2012)
      xp = data.frame(matrix(rep(xs[,3], ncol(t1s)), nrow=nrow(xs), ncol=ncol(t1s)))
      names(xp) = paste("nightlights", years.lst, sep=".")
      ## extrapolated values
      xp[sd.df,] = t1s
      ## add shift 0.5 cell
      xp$x <- xs$x+res(tif.r)[1]/2; xp$y <- xs$y
      xp.r = terra::rast(xp[,c("x","y",paste("nightlights", years.lst, sep="."))], type="xyz", crs="+proj=longlat +datum=WGS84 +no_defs")
      ## write each year as a tif
      x = parallel::mclapply(1:nlyr(xp.r), function(i){terra::writeRaster(xp.r[[i]], filename=out.tifs[i], gdal=c("COMPRESS=DEFLATE"), datatype='INT2U', NAflag=-32768, overwrite=FALSE)}, mc.cores = nlyr(xp.r))
      #gc()
    }
  }
}
stopCluster(cl)
gc()
## R CMD BATCH annual_lights.night_500m.R
