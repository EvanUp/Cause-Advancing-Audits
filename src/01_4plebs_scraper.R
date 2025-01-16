library(tidyverse)
library(fouRplebsAPI)

setwd('~/Projects/phd/4chan/HKSMR_audits/')
df <- read_csv('./data/search_engine_list.csv')
engines = df$`search engine`

for (engine in engines){
  SE <- search_4chan(boards = "pol", 
                            start_date = "2018-01-01", 
                            end_date = "2024-12-31", 
                            text = engine)
  write_csv(SE, paste0(paste0('raw/', engine), '.csv'))
  Sys.sleep(10)
}
