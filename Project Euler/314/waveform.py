import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def mirror(df, xmax=250):
    ### Make sure waveform is symmetrical by dropping all x > y and mirroring it ###
    df = df[df.y >= df.x].sort_values(by='x').drop_duplicates()
    if (df.x.iloc[-1] == df.y.iloc[-1]):   # No need to copy the last element as it will be duplicated then
        df2 = pd.DataFrame({'x': df.y.iloc[:-1][::-1],
                            'y': df.x.iloc[:-1][::-1]})
    else:
        df2 = pd.DataFrame({'x': df.y[::-1],
                            'y': df.x[::-1]})
    out = pd.concat([df, df2], ignore_index=True).reset_index(drop=True)
    return out
    
class Waveform:
    def __init__(self, x=250, x0=250, max_delta=0.5):   # Initialize as square
        assert (x >= 0) and (x <= 250), f"x must be between 0 and {250}. Was {x}"
        assert (x0 >= 0) and (x0 <= 250) and (x >= x0), f"x0 must be between 0 and {250} and be smaller than 'x'. Was {x0}"

        self.x = x
        self.x0 = x0
        self.max_delta = max_delta

        # Create initial waveform
        r = np.sqrt((250-x0)**2 + (x-x0)**2)
        x_coord = np.array(range(0, 250+1))
        y_circle = x0 + np.sqrt(r**2 - (x_coord-x0)**2)
        wf = pd.DataFrame({'x': x_coord, 'y_raw': y_circle})
        wf.loc[wf.x <= x,'y_raw'] = 250
        wf['y'] = wf.y_raw.apply(lambda x: int(round(x,0)))
        wf = wf.loc[abs(wf.y_raw - wf.y) <= max_delta]   # Remove points that are too far from the ideal curve
        wf = mirror(wf)

        self.wf = wf[['x', 'y']]
        self.perf = self.calc_performance()

    def calc_performance(self):
        area = (self.wf.x.diff()[1:] * self.wf.y.rolling(2).mean()[1:]).sum()
        length = np.sqrt(self.wf.x.diff()[1:]**2 + self.wf.y.diff()[1:]**2).sum() 
        return area/length

    def plot_waveform(self):
        all_points = pd.DataFrame([(x, y) for x in range(0,250+1) for y in range(0,250+1)], columns=['x', 'y'])
        fig1 = px.line(self.wf, x="x", y="y")
        fig2 = px.scatter(all_points, x="x", y="y")
        fig2.update_traces(marker=dict(size=1, color='black'))
        fig3 = go.Figure(data=fig1.data + fig2.data)
        fig3.update_layout(width=800, height=800)
        fig3.show()        

    def __repr__(self):
        return f"{self.__class__.__name__}({self.x}, {self.x0}, {self.max_delta})"

    def print_performance(self):
        print(self.perf)