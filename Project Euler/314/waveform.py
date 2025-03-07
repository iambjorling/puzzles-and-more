import pandas as pd
import numpy as np
import random
import plotly.express as px
import plotly.graph_objects as go

class Waveform:
    def __init__(self, wf=pd.DataFrame([], columns=['x','y'])):   # Initialize as square
        assert isinstance(wf, pd.DataFrame) and all(wf.columns.values == ['x', 'y']) and (wf.shape[1]==2), f"wf must be a pandas data frame with two columns, called x and y. Was {wf}"

        # Make sure waveform contains no duplicates and is symmetrical around the y=x line
        if (wf.shape[0]==0):
            self.wf = wf
            self.perf = None
        else:
            self.wf = Waveform.mirror(wf)
            self.perf = self.calc_performance()

    def copy(self):
        out = Waveform(self.wf.copy())
        return out

    def calc_performance(self):
        area = (self.wf.x.diff()[1:] * self.wf.y.rolling(2).mean()[1:]).sum()
        length = np.sqrt(self.wf.x.diff()[1:]**2 + self.wf.y.diff()[1:]**2).sum() 
        return area/length

    def move(self, x, n):
        # Moves the point at the x coordinate n steps up or down and recalculates performance
        wf = self.wf
        wf.loc[wf.x==x,'y'] = wf.loc[wf.x==x,'y'] + n # max(0,min(250,wf.loc[wf.x==x,'y'] + n))
        self.wf = Waveform.mirror(wf)
        self.perf = self.calc_performance()

    def drop_point(self, x):
        # Removes the point at x=x from the waveform and recalculates performance
        wf = Waveform.mirror(self.wf[self.wf.x != x])
        self.wf = wf
        self.perf = self.calc_performance()

    def move_up(self, x, n=1):
        # Moves the point at the x coordinate n steps UP and recalculates performance
        self.move(x,abs(n))
    
    def move_down(self, x, n=1):
        # Moves the point at the x coordinate n steps DOWN and recalculates performance
        self.move(x,-abs(n))

    def add_point(self, x):
        # Adds a point at x, y value set as linear interpolation between adjacent values
        
        # Find the points right to the left and right of the x value
        i_left = np.max(np.where(self.wf.x < x))
        i_right = np.min(np.where(self.wf.x > x))
        
        # Do an interpolation of these points' y values
        k = (self.wf.y[i_left]-self.wf.y[i_right])/(self.wf.x[i_left]-self.wf.x[i_right])
        m = self.wf.y[i_left] - k*self.wf.x[i_left]
        # print(k, m)
        y_new = round(k*x + m)

        # Set the new point and caclulate performance
        wf = Waveform.mirror(pd.concat([self.wf, pd.DataFrame({'x':x, 'y':y_new},index=[0])], ignore_index=True))
        self.wf = wf
        self.perf = self.calc_performance()

    
    @staticmethod
    def mirror(df):
        ### Make sure waveform is symmetrical by dropping all x > y and mirroring it ###
        if df.shape==(0, 0):
            return(df)
        else:
            df = df[df.y >= df.x].sort_values(by='x').drop_duplicates()
            if (df.x.iloc[-1] == df.y.iloc[-1]):   # Do not copy the last element as it then will be duplicated
                df2 = pd.DataFrame({'x': df.y.iloc[:-1][::-1],
                                    'y': df.x.iloc[:-1][::-1]})
            else:
                df2 = pd.DataFrame({'x': df.y[::-1],
                                    'y': df.x[::-1]})
            out = pd.concat([df, df2], ignore_index=True).reset_index(drop=True)
            return out

    @staticmethod
    def alter_and_return_best(wf, x, verbose=True):
        # Alters the waveform in 4 ways and returns the best one
        # The point at x=x is either moved up 1 sample, moved down 1 sample, removed or left as it is
        # If there is no point at x, a point is added at x at an y value interpolated from the neighboring points and then as above
    
        current_wf = wf.copy()
        max_perf = current_wf.perf
    
        # Create the waveform wf_no_move (as is, or adding y between adjacent values 
        # if no point) and wf_dropped (dropping x coordinate)
        x_is_missing = ((current_wf.wf.x == x).sum() == 0)
        if x_is_missing:
            wf_dropped = current_wf.copy()
            wf_no_move = current_wf.copy()
            wf_no_move.add_point(x)
        else: 
            wf_no_move = current_wf.copy()
            wf_dropped = current_wf.copy()
            wf_dropped.drop_point(x)
    
        # Calc performance for plus 1 and minus 1
        wf_plus_1 = wf_no_move.copy()
        wf_plus_1.move_up(x,1)
        wf_minus_1 = wf_no_move.copy()
        wf_minus_1.move_down(x,1)
    
        # Select the best new waveform and update variables
        perf_list = [wf_no_move.perf, wf_dropped.perf, wf_plus_1.perf, wf_minus_1.perf]
        max_index = perf_list.index(max(perf_list))
        if (max_index == 0):
            best_wf = wf_no_move.copy()
            max_perf = wf_no_move.perf
            if x_is_missing:
                if verbose:
                    print('Found a better one, perf =', f"{max_perf:.8f}")
        
        elif (max_index == 1):
            best_wf = wf_dropped.copy()
            max_perf = wf_dropped.perf
            if not x_is_missing:
                if verbose:
                    print('Found a better one, perf =', f"{max_perf:.8f}")
    
        elif (max_index == 2):
            best_wf = wf_plus_1.copy()
            max_perf = wf_plus_1.perf
            if verbose: 
                print('Found a better one, perf =', f"{max_perf:.8f}")
        else:
            best_wf = wf_minus_1.copy()
            max_perf = wf_minus_1.perf
            if verbose: 
                print('Found a better one, perf =', f"{max_perf:.8f}")
    
        return best_wf    

    def add_noise(self, sigma=2, min_x=0):
        # Adds noise to the waveform
        
        # n_non_empty = self.wf[self.wf.x <= self.wf.y].x.count()
        r_empty = 1-self.wf[self.wf.x <= self.wf.y].shape[0]/251    # NOT CORRECT, BUT WHATEVER

        # Add points to make waveform complete
        new_y = np.interp(range(251), self.wf.x, self.wf.y)
        new_wf = pd.DataFrame({'x':range(251), 'y':new_y})
        new_wf = new_wf[new_wf.x <= new_wf.y]

        # Add noise
        new_wf.loc[min_x::,'y'] = np.minimum(250, new_wf.loc[min_x::,'y'] + [round(random.gauss(0, sigma)) for i in range(min_x, new_wf.shape[0])])

        # Remove random points to make it the same size as from the start
        # Always make sure 0,250 is still there
        new_wf = pd.concat([new_wf.sample(frac=r_empty), pd.DataFrame({'x':0, 'y':250}, index=[0])],ignore_index=True)
        new_wf['x'] = new_wf.x.apply(int)
        new_wf['y'] = new_wf.y.apply(int)

        # Mirror and set waveform
        self.wf = Waveform.mirror(new_wf)
        self.perf = self.calc_performance()
            

    def plot_waveform(self):
        all_points = pd.DataFrame([(x, y) for x in range(0,250+1) for y in range(0,250+1)], columns=['x', 'y'])
        fig1 = px.line(self.wf, x="x", y="y")
        fig2 = px.scatter(all_points, x="x", y="y")
        fig2.update_traces(marker=dict(size=1, color='black'))
        fig3 = go.Figure(data=fig1.data + fig2.data)
        fig3.update_layout(width=800, height=800)
        fig3.show()

    def plot_waveforms(self, list_of_wf_objects, name_of_objects=[], plot_points=True):
        # Create plot_data
        plot_data = self.wf.copy()
        if len(name_of_objects) == 0:
            plot_data['Waveform'] = 'Waveform 1' + ' (' + f"{self.perf:.8}" + ')'
        else:
            plot_data['Waveform'] = name_of_objects[0] + ' (' + f"{self.perf:.8}" + ')'
        for ind, item in enumerate(list_of_wf_objects):
            temp = item.wf.copy()
            if len(name_of_objects) == 0:
                temp['Waveform'] = temp['Waveform'] = 'Waveform ' + str(ind+2) + ' (' + f"{list_of_wf_objects[ind].perf:.8}" + ')'
            else:
                temp['Waveform'] = name_of_objects[ind+1] + ' (' + f"{list_of_wf_objects[ind].perf:.8}" + ')'
            plot_data = pd.concat([plot_data, temp], ignore_index=True)
        
        # Create coordinates of points
        all_points = pd.DataFrame([(x, y) for x in range(0,250+1) for y in range(0,250+1)], columns=['x', 'y'])

        # Plot data
        fig1 = px.line(plot_data, x="x", y="y", color='Waveform', markers=True)
        if plot_points:
            fig2 = px.scatter(all_points, x="x", y="y")
            fig2.update_traces(marker=dict(size=1, color='black'))
            fig1 = go.Figure(data=fig1.data + fig2.data)
        fig1.update_layout(width=800, height=700)
        fig1.show()
        
    def __repr__(self):
        return f"{self.__class__.__name__}({self.wf})"

    def __str__(self):
        return('Waveform with ' + str(self.wf.shape[0]) + ' points. Area to circumference ratio = ' + str(self.perf))

    def print_performance(self):
        print(f"{self.perf:.8f}")
        # print(self.perf)