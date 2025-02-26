# ------------------------------------------------------------------------------
# This notebook runs a Cpp simulation of the Project Euler problem 151. It 
# performs the following steps:
#   
# * Runs the simulation
# * Plots the results
# * Stores the simulation results in a text file
# * Calculates the average value and 95% CI
# * Estimates the time required to get 5e-9 precision
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# Set packages and constants
# ------------------------------------------------------------------------------
library(Rcpp)
library(ggplot2)

N_TRIPS <- 1e8
MAX_N_PLATES <- 1e4
SAVE_FNAME <- "R simulation output.csv"
FILE_PATH <- "C:/git-repos/puzzles-and-more/Project Euler/371/"
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# Define Cpp function
# ------------------------------------------------------------------------------
cppFunction('
#include <Rcpp.h>
using namespace Rcpp;

// [[Rcpp::export]]
IntegerVector cpp_function(int n_trips, int max_n_plates) {
    // Initialize output vector
    IntegerVector out(max_n_plates, 0);
    int trip_done;
    int n_seen;
    int x;   // The seen plate
    
    // Loop over all trips
    for (int i = 0; i < n_trips; i++) {
        // Initialize variables
        LogicalVector plates_seen(1000, false);
        n_seen = 0;
        x = rand() % 1000;  // Generate first plate
        trip_done = 0;
        
        // If the first is a 500 plate, then we check once more since we need to 
        // see two 500 plates
        if (x == 500) {
            plates_seen[x] = true;
            n_seen++;
            x = rand() % 1000;  // Generate a new plate
        }

        // Loop until we have a 1000 sum
        while (trip_done == 0) {
            if ((x != 0) && (plates_seen[1000-x])) {
                trip_done = 1;
            } else {
              plates_seen[x] = true;
              n_seen++;
  
              // Generate a new plate
              x = rand() % 1000;
            }
        }

        // Store the number of plates it took for this trip
        if (n_seen < max_n_plates) {
            out[n_seen]++;
        }
    }

    return out;
}')

# temp <- cpp_function(1000, 10000)
# sum(temp)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# Do a simulation with the Rcpp function
# ------------------------------------------------------------------------------
cat(paste0(format(Sys.time()), ' Starting simulation (N_TRIPS = ', N_TRIPS, ')\n'))
start_cpp <- Sys.time()
temp <- cpp_function(N_TRIPS, MAX_N_PLATES)  # 1e8 took 131 seconds
end_cpp <- Sys.time()
t_execution <- as.numeric(difftime(end_cpp, start_cpp, units='mins'))
cat(paste0(format(Sys.time()), '. Done. Took ', round(t_execution,1), ' minutes\n\n'))
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# Plot the results
# ------------------------------------------------------------------------------
plot_data <- data.frame(n_plates=1:MAX_N_PLATES, n_trips=temp, r_trips=temp/sum(temp))
plot_data <- plot_data[1:max(which(plot_data$n_trips != 0)),]
avg_n_plates <- sum(plot_data$n_plates*plot_data$r_trips)
p <- ggplot(data=plot_data, aes(x=n_plates, y=r_trips)) +
  geom_point() +
  geom_line() +
  ggtitle(paste0('Simulated ',
                 format(N_TRIPS, big.mark = " ", scientific=FALSE),
                 ' trips\nAverage number of plates = ', avg_n_plates)) +
  scale_y_continuous(labels = scales::percent)
print(p)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# Store results in file
# ------------------------------------------------------------------------------
write.csv(plot_data, file=paste0(FILE_PATH, SAVE_FNAME), row.names=FALSE)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# Calculate average, confidence interval etc
# ------------------------------------------------------------------------------
m <- sum(plot_data$n_plates*plot_data$r_trips)
s <- sqrt(sum(plot_data$r_trips*(plot_data$n_trips-m)^2)/(sum(plot_data$n_trips)-1))
ci <- 1.96*s/sqrt(sum(plot_data$n_trips))

# Calculate expected time.
# 2*ci = 5e-9 =>2*1.96*s/sqrt(n) => n = (2*1.96*s/5e-9)^2
n_required <- (2*1.96*s/5e-9)^2
t_required <- t_execution/N_TRIPS*n_required

cat(paste0('Average number of plates seen: ', round(m,8), ' +/-', round(ci,8), '\n'))
cat(paste0('Required time to get 5e-9 precision: ', formatC(as.numeric(ceiling(t_required/60/24)), format="f", digits=0, big.mark=" "), ' days (sic!)'))
# ------------------------------------------------------------------------------