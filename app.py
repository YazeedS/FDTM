from flask import Flask, render_template, request, url_for, send_file
import pandas as pd
import math
import re
from IPython.display import HTML
import matplotlib.pyplot as plt
from PIL import Image
import io
import base64



app=Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/raw")
def raw_data():
    return render_template("raw_data.html")

@app.route("/cb")
def cb_freq():
    return render_template("cb_freq.html")

@app.route("/oraganizing", methods=["post"])
def organize_cbfreq():
    if request.method == "POST":

        k = request.form["k"]
        # for loop with k to get all the variables inside
        htmls=[]
        for x in range(int(k)):
            row=[HTML(f'<td><input type="number" name="lowerBoundry{x}" placeholder="Lower Boundry" required></td>'),
            HTML(f'<td><input type="number" name="higherBoundry{x}" placeholder="Higehr Boundry" required></td>'),
            HTML(f'<td><input type="number" name="frequency{x}" placeholder="Frequency" required></td>')]

            htmls.append(row)


    return render_template("EnterCB.html", k=int(k), htmls=htmls)


@app.route("/table", methods=["post"])
def construct_table():

    if request.method == "POST":
        #if the data is raw
        try:
            data_string = request.form["data"]
            #delete all spaces , seperate columns, delete anything that is not numbers or commas
            data = re.findall(r"\d+", data_string)

            n = len(data)

            data = [float(x) for x in data]

            x_small = min(data)
            x_large = max(data)
            t_range = x_large-x_small
            k = int(3.322 * math.log(n, 10))
            c = math.ceil((t_range + 1) / k)
            lower_boundry = x_small

            data_table = {"Class Limit": [], "Class Boundries": [], "Class Midpoint": [], "Frequency": [],"Relative Frequency": [], "ACF":[] , "DCF": []}

            acf = 0
            dcf = n
            #Adding data to the table
            for x in range(k):
                #Class Limit
                higher_boundry = lower_boundry+c-1
                data_table["Class Limit"].append("{} - {}".format(lower_boundry, higher_boundry))

                #Class Boundries
                data_table["Class Boundries"].append("{} → {}".format(lower_boundry-0.5, higher_boundry + 0.5))

                #Mid Point
                data_table["Class Midpoint"].append((lower_boundry+higher_boundry)/2)

                #Frequency
                frequency=0
                for number in data:
                    if number >= (lower_boundry-0.5) and number < (higher_boundry+0.5):
                        frequency+=1
                data_table["Frequency"].append(frequency)

                #Relative Frequency
                rf = frequency/n
                data_table["Relative Frequency"].append(rf)

                #ACF
                acf+=frequency
                data_table["ACF"].append(acf)

                #DCF
                data_table["DCF"].append(dcf)
                dcf-=frequency

                #iterative stuff
                lower_boundry = lower_boundry + c

        #if the data is cb and freq
        except:
            data = {"Class Boundries": [], "Frequency": []}

            ##This hall section is just to get k
            i=0
            condition=False
            while True:
                try:
                    notk = request.form[f"lowerBoundry{i}"]
                except:
                    condition=True
                finally:
                    if condition==True:
                        k=i
                        break
                    else:
                        i+=1
            #until here

            for i in range(k):
                data["Class Boundries"].append("{} → {}".format(request.form[f"lowerBoundry{i}"], request.form[f"higherBoundry{i}"]))
                data["Frequency"].append(request.form[f"frequency{i}"])


            n = sum([int(x) for x in data["Frequency"]])

            data_table = {"Class Limit": [], "Class Boundries": [], "Class Midpoint": [], "Frequency": [],"Relative Frequency": [], "ACF":[] , "DCF": []}

            acf = 0
            dcf = n
            c = float(data["Class Boundries"][0].split()[2]) - float(data["Class Boundries"][0].split()[0])


            #Adding data to the table
            for x in range(int(k)):
                #Class Limit
                lower_boundry = float(data["Class Boundries"][x].split(" → ")[0])
                higher_boundry = float(data["Class Boundries"][x].split(" → ")[1])
                frequency = int(data["Frequency"][x])

                data_table["Class Limit"].append("{} - {}".format(lower_boundry+0.5, higher_boundry-0.5))

                #Class Boundries
                data_table["Class Boundries"].append("{} → {}".format(lower_boundry, higher_boundry))

                #Mid Point
                data_table["Class Midpoint"].append((lower_boundry+higher_boundry)/2)

                #Frequency
                data_table["Frequency"].append(frequency)

                #Relative Frequency
                rf = frequency/n
                data_table["Relative Frequency"].append(rf)

                #ACF
                acf+=frequency
                data_table["ACF"].append(acf)

                #DCF
                data_table["DCF"].append(dcf)
                dcf-=frequency

            #turning the variable data into a list of number so that the histogram can deal with
            data=[]
            for x in range(k):
                for y in range(data_table["Frequency"][x]):
                    data.append(data_table["Class Midpoint"][x])

        finally:

            df_show = pd.DataFrame(data=data_table)
            df = df_show

            df_show = df_show.append({'Class Limit' : 'TOTAL' , 'Class Boundries' : "━━━━━", "Class Midpoint": "━━",
            "Frequency": n, "Relative Frequency": 1.0, "ACF": "━", "DCF":"━"} , ignore_index=True)
            #NOW we got the table ready in a pandas data frame, we must show it in the index file

            #Central Tendency

            #1 Mean
            summed = 0
            for x in range(k):
                summed += (df["Frequency"][x]*df["Class Midpoint"][x])

            mean = summed/n

            #2 Median
            possible_acfs = [x for x in df["ACF"] if x >= (n/2)]
            class_index = data_table["ACF"].index(possible_acfs[0])
            median_class = df.iloc[[class_index]]

            median_class_lb = float(data_table["Class Boundries"][class_index].split(" → ")[0])
            class_frequency = data_table["Frequency"][class_index]
            class_acf = data_table["ACF"][class_index]

            median = median_class_lb + ((n/2 - (class_acf-class_frequency))/class_frequency) * c

            #3 Mode

            if k < 3:
                mode="No Mode"
            else:
                possible_freq_index = []
                for i in range(1, k-1):
                    if data_table["Frequency"][i] >= data_table["Frequency"][i-1] and data_table["Frequency"][i] >= data_table["Frequency"][i+1]:
                        possible_freq_index.append(i)

                #if there is only one possilbe frequency then there's only one mode
                if len(possible_freq_index) == 0:
                    mode="No mode"

                elif len(set(data_table["Frequency"])) == 1:
                    mode="No mode, uniform"

                #if there is 2 peakes next to each other



                else:
                    class_modal = df.iloc[[possible_freq_index[0]]]
                    class_frequency = data_table["Frequency"][class_index]
                    d1 = class_frequency - data_table["Frequency"][class_index-1]
                    d2 = class_frequency - data_table["Frequency"][class_index+1]
                    class_modal_lb = float(data_table["Class Boundries"][class_index].split(" → ")[0])

                    mode = round(((class_modal_lb + (d1/(d1+d2)) * c)), 2)

                #elif len(possible_freq_index) == len(set(possible_freq_index)):
                #else:
                #    mode="This will be fixed"


            #Measures of dispersion and variance

            #1 Standerd Deviation & Variance
            variance = 0
            for x in range(k):
                variance += data_table["Frequency"][x]* ((data_table["Class Midpoint"][x] - mean)**2)

            variance = variance / (n-1)
            standerd_deviation = abs(variance**(1/2))


            #2 Range
            Range = df["Class Midpoint"][k-1] - df["Class Midpoint"][0]

            #3 Coeffecient of Variation
            cv = standerd_deviation / mean * 100

            ####
            #Graphs
            ####

            #the function that makes graphs useable in HTML
            def fig_to_base64(fig):
                img = io.BytesIO()
                fig.savefig(img, format='png',
                            bbox_inches='tight')
                img.seek(0)

                return base64.b64encode(img.getvalue())

            #Plotting the Histogram
            class_boundries = []

            for x in range(k):
                class_boundries.append(float(data_table["Class Boundries"][x].split()[0]))

                if x == (k-1):
                    class_boundries.append(float(data_table["Class Boundries"][x].split()[2]))

            fig, ax = plt.subplots()
            plt.hist(data, bins=class_boundries, color="#ff9999")

            plt.title("Histogram")
            plt.ylabel("Frequency")
            plt.xlabel("Class Boundries")
            plt.grid(True)
            plt.xticks(class_boundries)

            encoded = fig_to_base64(fig)
            histogram = '<img src="data:image/png;base64, {}" , height="400" width="400" align="center">'.format(encoded.decode('utf-8'))

            #Plotting the polygon
            plt.clf()
            #getting the coordinates
            poly_x = [data_table["Class Midpoint"][0]-c]
            poly_y = [0]
            for x in range(k):
                poly_x.append(data_table["Class Midpoint"][x])
                poly_y.append(data_table["Frequency"][x])


            poly_x.append(data_table["Class Midpoint"][k-1]+c)
            poly_y.append(0)
            #plotting the line
            plt.plot(poly_x, poly_y, color='#ff9999', alpha=0.7,
                linewidth=3, solid_capstyle='round', zorder=2)
            #filled circles
            plt.scatter(data_table["Class Midpoint"], data_table["Frequency"], s=100, color="b")

            #open circles from the two sides
            plt.scatter(poly_x[0], 0, color="b", facecolors='none', s=100)
            plt.scatter(poly_x[k+1], 0, color="b", facecolors='none', s=100)
            #syle
            plt.xticks(poly_x)
            plt.yticks(poly_y)
            plt.title("Polygon")
            plt.xlabel("Class Midpoint")
            plt.ylabel("Frequency")

            encoded = fig_to_base64(fig)
            polygon = '<img src="data:image/png;base64, {}" , height="400" width="400" align="center">'.format(encoded.decode('utf-8'))

            # Plotting the ACFP
            plt.clf()
            acf_x = []
            acf_y = [0]
            for x in range(k):
                acf_x.append(float(data_table["Class Boundries"][x].split(" → ")[0]))
                acf_y.append(data_table["ACF"][x])

            acf_x.append(float(data_table["Class Boundries"][k-1].split(" → ")[1]))


            plt.plot(acf_x, acf_y, color='#ff9999', alpha=0.7,
                 linewidth=3, solid_capstyle='round', zorder=2)

            plt.scatter(acf_x, acf_y, s=50, color="b")


            plt.xticks(acf_x)

            plt.title("Ascending Cumulative Frequency Polygon (ACFP)")
            plt.xlabel("Class Boundreies")
            plt.ylabel("ACF")

            encoded = fig_to_base64(fig)
            acfp = '<img src="data:image/png;base64, {}" , height="400" width="400" align="center">'.format(encoded.decode('utf-8'))

            #Plotting the DFCP
            plt.clf()

            dcf_x = []
            dcf_y = []

            for x in range(k):
                dcf_x.append(float(data_table["Class Boundries"][x].split(" → ")[0]))
                dcf_y.append(data_table["DCF"][x])

            dcf_x.append(float(data_table["Class Boundries"][k-1].split(" → ")[1]))
            dcf_y.append(0)

            plt.plot(dcf_x, dcf_y, color='#ff9999', alpha=0.7,
                 linewidth=3, solid_capstyle='round', zorder=2)

            plt.scatter(dcf_x, dcf_y, s=50, color="b")

            plt.xticks(dcf_x)

            plt.title("Descending Cumulative Frequency Polygon (ACFP)")
            plt.xlabel("Class Boundreies")
            plt.ylabel("DCF")

            encoded = fig_to_base64(fig)
            dcfp = '<img src="data:image/png;base64, {}" , height="400" width="400" align="center">'.format(encoded.decode('utf-8'))


            return render_template('table.html',  tables=[HTML(df_show.to_html(classes='table table-striped table-dark', justify='center',index=False))],
             titles=df.columns.values,
            mean = round(mean,2) , median = round(median,2), mode=mode,
            variance= round(variance,2), standerd_deviation=round(standerd_deviation, 2),
            Range = round(Range, 2), cv = round(cv, 2), histogram=HTML(histogram), polygon=HTML(polygon),
            acfp=HTML(acfp), dcfp=HTML(dcfp))

if __name__ == '__main__':
    app.debug=True
    app.run()
