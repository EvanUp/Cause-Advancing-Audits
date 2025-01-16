library(tidyverse)
library(lubridate)

setwd('~/Projects/phd/4chan/HKSMR_AUDITS/')
ec <- read_csv('data/processed/data_with_ec.csv')
gpt4_engine_ranks <- read_csv('data/annotations/GPT_Annotations/annotationsv1/gpt4_engine_ranks.csv')
query <- read_csv('data/annotations/GPT_Annotations/annotationsv1/gpt4_query.csv')
TOP_5 <- TRUE
# extract random sample to annotate
#out <- ec %>% sample_n(25)
#out <- out %>% select(unique_index, comments)
#write_csv(out, '4chan_annotation_sample.csv')

#### GENERATING FIGURE 1
# Convert the timestamp and remove noisy comments
df <- ec %>%
  mutate(timestamp = as_datetime(timestamp)) %>%
  mutate(monthly = floor_date(timestamp, "month")) %>% 
  filter(engine_comparison == "yes") %>% distinct()

monthly_total <- df %>% select(monthly, doc_id) %>% 
  distinct() %>% 
  mutate(dummy = 1) %>% 
  group_by(monthly) %>% 
  summarize(count = sum(dummy))
mean(monthly_total$count)


if (TOP_5 == TRUE){
  # Aggregate counts by month for each 1-hot-encoded column
  SEs = colnames(df)[21:49]
  sedf <- df[SEs]
  sedf$monthly <- df$monthly
  monthly_counts <- sedf %>%
    group_by(monthly) %>%
    summarise(across(SEs, sum))
  
  other <- names(sort(colSums(monthly_counts[2:30])))[1:24]
  major <- names(sort(colSums(monthly_counts[2:30])))[25:29]
  major <- c('monthly', major)
  other_vals <- monthly_counts[,other] %>% rowSums()
  monthly_counts <- monthly_counts[major]
  monthly_counts['other search engines'] <- other_vals
  # top 5: google, yandex, startpage, duckduckgo, bing, searx, qwant
  color_palette <- c("#000000","#043673","#009647", "grey33", "#FDB515", "#C41230")
} else{
  SEs = colnames(df)[21:49]
  sedf <- df[SEs]
  sedf$monthly <- df$monthly
  monthly_counts <- sedf %>%
    group_by(monthly) %>%
    summarise(across(SEs, sum))
  
  min(rowSums(monthly_counts[2:30]))
  max(rowSums(monthly_counts[2:30]))
  mean(rowSums(monthly_counts[2:30]))
}


monthly_counts_long <- monthly_counts %>%
  pivot_longer(-monthly, names_to = "Search Engine", values_to = "count")


events <- data.frame(
  event_date = as.Date(c('2020-03-01', '2020-12-01')),
  event_label = c('Event A', 'Event B')
)

#### GENERATE FIGURE 1 (LEFT)
ggplot(monthly_counts_long, aes(x = monthly, y = count, color = `Search Engine`)) +
  geom_line(size = 1.5, alpha = 0.9) +
  #geom_line()+
  theme(panel.grid.major = element_blank(), panel.grid.minor = element_blank(),
        panel.background = element_blank(), axis.line=element_line(color='black'))+
  theme(text = element_text(size = 35),
        legend.text=element_text(size=35),
        axis.title.y = element_text(size=35),
        axis.title.x = element_text(size=35),
        plot.title = element_text(hjust = 0.5),
        legend.position=c(0.85, 0.70)) +
  scale_x_datetime(date_breaks = "1 year",date_labels = "%Y")+
  geom_vline(data = events, aes(xintercept = as.POSIXct(c("2020-03-01", "2020-12-01"))), linetype = "dashed", color = "red") +
  annotate("text", x = as.POSIXct("2020-02-05"), y = 300, 
           label = "COVID-19 Lockdowns Begin", color = "red", angle = 90, vjust = -0.5, size = 8) +
  annotate("text", x = as.POSIXct("2020-12-01"), y = 300, 
           label = "Vaccine Rollouts Begin", color = "red", angle = 90, vjust = -0.5, size = 8) +
  scale_y_continuous(expand = c(0, 0), limits = c(0, 400)) +  # Set y-axis limit to 150
  #scale_y_log10(expand = c(0, 0), limits = c(1, 400)) +  # Log scale and updated limits
  scale_color_manual(values =color_palette)+
  #scale_x_discrete(limits=c("2018","2019","2020", "2021", "2022", "2023", "2024"))+
  xlab('')+
  ylab('')+
  ggtitle('Monthly comments comparing at least 3 search engines on /pol/')
  
ggsave('./results/3se_audits.png', width=20, height=12, dpi=300)


##### GENERATE FIGURE 1 (RIGHT)

monthly_counts_long2 <- monthly_counts_long %>%
  group_by(`Search Engine`) %>%
  mutate(count_smooth = zoo::rollmean(count, k = 3, fill = NA, align = "center"))#,
         #count_smooth = replace_na(count_smooth, 1))  # Replace NA with 1
# Create Figure 1
ggplot(monthly_counts_long2, aes(x = monthly, y = count_smooth+1, color = `Search Engine`)) +
  geom_line(size = 1.5, alpha = 0.9) +
  #geom_smooth(method = "loess", span = 0.3, size = 1.5, alpha = 0.9, se = FALSE) +  # Adjust span for smoothness
  #geom_line()+
  theme(panel.grid.major = element_blank(), panel.grid.minor = element_blank(),
        panel.background = element_blank(), axis.line=element_line(color='black'))+
  theme(text = element_text(size = 35),
        legend.text=element_text(size=35),
        axis.title.y = element_text(size=20),
        axis.title.x = element_text(size=35),
        plot.title = element_text(hjust = 0.5),
        legend.position=c(0.85, 0.85)) +
  scale_x_datetime(date_breaks = "1 year",date_labels = "%Y")+
  geom_vline(data = events, aes(xintercept = as.POSIXct(c("2020-03-01", "2020-12-01"))), linetype = "dashed", color = "red") +
  annotate("text", x = as.POSIXct("2020-01-05"), y = 90, 
           label = "COVID-19 Lockdowns Begin", color = "red", angle = 90, vjust = -0.5, size = 8) +
  annotate("text", x = as.POSIXct("2020-11-01"), y = 90, 
           label = "Vaccine Rollouts Begin", color = "red", angle = 90, vjust = -0.5, size = 8) +
  #scale_y_continuous(expand = c(0, 0), limits = c(0, 400)) +  # Set y-axis limit to 150
  scale_y_log10(expand = c(0, 0), limits = c(1, 400)) +  # Log scale and updated limits
  scale_color_manual(values =color_palette)+
  #scale_x_discrete(limits=c("2018","2019","2020", "2021", "2022", "2023", "2024"))+
  xlab('')+
  ylab('Mention Count (log scale)')+
  ggtitle('Number of comments comparing at least 3 search engines on /pol/\n3-month rolling mean')+
 lemon::coord_capped_cart(bottom = 'both', left = 'both')

ggsave('./results/3se_audits_rolling.png', width=20, height=12, dpi=300)

## GENERATING TABLE 1
ectrunc <- ec %>% select(unique_index, engine_comparison) %>% distinct()
gpt4_engine_ranks <- gpt4_engine_ranks %>% 
  drop_na() %>% 
  left_join(ectrunc, by = c("idx" = "unique_index"))
# clean up gpt4o-mini ranks
g4er <- gpt4_engine_ranks %>%
  drop_na() %>% 
  filter(engine_comparison == 'yes') %>% 
  mutate(engine = tolower(engine)) %>% 
  mutate(engine = if_else(engine == "yandex.com", "yandex", engine)) %>% 
  mutate(engine = if_else(engine == "yandex.ru", "yandex", engine)) %>% 
  mutate(engine = if_else(engine == "duckduckgo.com", "duckduckgo", engine)) %>% 
  mutate(engine = if_else(engine == "yahoojapan", "yahoo", engine)) %>% 
  mutate(engine = if_else(engine == "starpage", "startpage", engine)) %>% 
  mutate(engine = if_else(engine == "intelx.io", "intelx", engine)) %>% 
  mutate(engine = if_else(engine == "yahoo.com", "yahoo", engine)) %>% 
  mutate(engine = if_else(engine == "gigablast.com", "gigablast", engine)) %>% 
  mutate(engine = if_else(engine == "bravesearch", "brave search", engine)) %>% 
  mutate(engine = if_else(engine == "brave", "brave search", engine)) %>% 
  mutate(engine = if_else(engine == "ddg", "duckduckgo", engine)) %>%   
  mutate(engine = if_else(engine == "sears.me", "searx", engine)) %>% 
  mutate(engine = if_else(engine == "searx.me", "searx", engine)) %>% 
  mutate(engine = if_else(engine == "jewgle", "google", engine)) 
  
# top ranks
r1 = g4er %>% filter(rank == 1) %>% group_by(engine) %>% count(sort = T)

#worst ranks
worst <- g4er %>%
  group_by(idx) %>%           
  filter(rank == max(rank)) %>%   # Filter rows where 'rank' is the minimum for that 'idx'
  ungroup() %>% 
  group_by(engine) %>% count(sort = T)


colnames(r1) <- c('engine', 'top')
colnames(worst) <-c('engine', 'bottom')
together = r1 %>% left_join(worst, by = 'engine')
together$difference = together$top - together$bottom
colnames(together) <- c('engine','top_ranked', 'bottom_ranked', 'difference')
together

write_csv(together,'results/audit_winners_v1.csv')
head(together, 30)

## Query stats
query_full <- query %>% left_join(ectrunc, by = c("idx" = "unique_index"))
directives <- query_full %>% drop_na() %>% group_by(`query`) %>% count(sort = T)
