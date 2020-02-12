from flask import Flask, render_template, request, url_for, send_file
import pandas as pd
import math
import re
from IPython.display import HTML
import matplotlib.pyplot as plt
from PIL import Image
import io
import base64
from random import randint



app=Flask(__name__)

@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/upload")
def upload():
    return render_template("upload.html")

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
        htmls=[[HTML(f'<td><input id="lower" type="text" name="lowerBoundry{0}" placeholder="Lower Boundry" required></td>'),
        HTML(f'<td><input id="higher" type="text" name="higherBoundry{0}" placeholder="Higehr Boundry" required></td>'),
        HTML(f'<td><input type="number" name="frequency{0}" placeholder="Frequency" min=1 required></td>')]]
        for x in range(1, int(k)):

            row=[HTML(f'<td></td>'),
            HTML(f'<td></td>'),
            HTML(f'<td><input type="number" name="frequency{x}" placeholder="Frequency" min=1 required></td>')]

            htmls.append(row)


    return render_template("EnterCB.html", k=int(k), htmls=htmls)


@app.route("/table", methods=["post"])
def construct_table(data=[], ques=""):

        #if the data is raw
    try:
        try:
            type="raw"
            data_string = request.form["data"]

            junk = re.findall(r"\D", data_string)
            junk = [x for x in junk if x not in ["-", "."]]

            for x in range(len(junk)):
                data_string = data_string.replace(junk[x], " ")
            data=[]
            data_string = data_string.split()
            for number in data_string:
                try:
                    data.append(float(number))
                except:
                    pass
        except:
             data = data
        finally:
            n = len(data)

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

            #Creating the string that will be displayed on top of the table.
            numbers_string=f"The following calculations are based on {n} values: "
            if n == 2:
                numbers_string+= str(data[0])+ " and "+str(data[1])
            else:
                for number in range(n-1):
                    numbers_string+= str(data[number]) + ", "
                numbers_string+= "and " + str(data[-1])


    #if the data is cb and freq
    except:
        type="cb_freq"
        data = {"Class Boundries": [], "Frequency": []}

        ##This hall section is just to get k
        i=0
        condition=False
        while True:
            try:
                notk = request.form[f"frequency{i}"]
            except:
                condition=True
            finally:
                if condition==True:
                    k=i
                    break
                else:
                    i+=1
        #until here

        #Trying to find if the inputted boundries are valid

        try:
            float(request.form["lowerBoundry0"])
            float(request.form["higherBoundry0"])
            type="cb_freq"
        except ValueError:
            type="cb_freq_invalid"

        except:
            #Because there's is a conflict with the case of 1 value in raw data and invalid class boundry
            data=[1]
        if type=="cb_freq":
            for i in range(k):
                if i == 0:
                    data["Class Boundries"].append("{} → {}".format(request.form[f"lowerBoundry{i}"], request.form[f"higherBoundry{i}"]))
                    data["Frequency"].append(request.form[f"frequency{i}"])
                else:
                    data["Frequency"].append(request.form[f"frequency{i}"])

                c = float(data["Class Boundries"][0].split()[2]) - float(data["Class Boundries"][0].split()[0])
                higher = float(data["Class Boundries"][0].split()[2])

                for i in range(1, k):
                    data["Class Boundries"].append("{} → {}".format(higher, higher+c))
                    higher+=c

            n = sum([int(x) for x in data["Frequency"]])

            data_table = {"Class Limit": [], "Class Boundries": [], "Class Midpoint": [], "Frequency": [],"Relative Frequency": [], "ACF":[] , "DCF": []}

            acf = 0
            dcf = n

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

            #Defining numbers_string incase it's cb Frequency
            numbers_string = ""
            #Defining C so that it can be used in the second elif after the finally statment


    finally:
        #if the class Boundries are invalid
        if type=="cb_freq_invalid":
            return render_template("index.html", message=HTML('<div class="alert alert-danger" role="alert">Please enter valid class boundries!</div>'), condition=True)
        #if the user enterd only one value, raw or cb_freq
        elif len(data) < 2:
            return render_template("index.html", message=HTML('<div class="alert alert-danger" role="alert">Please enter more than one value!</div>'), condition=True)
        #if the lower is less than higher
        elif lower_boundry >= higher_boundry and type=="cb_freq":
            return render_template("index.html", message=HTML('<div class="alert alert-danger" role="alert">The lower boundry has to be lower than the higher boundry!</div>'), condition=True)
        #if the length of the class is not an integer in cb_freq
        elif int(c) != float(c):
            return render_template("index.html", message=HTML('<div class="alert alert-danger" role="alert">The length of the class has to be an integer!</div>'), condition=True)
        #if it's all good
        else:
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
                mode_string="No Mode"
            else:
                possible_freq_index = []
                for i in range(1, k-1):
                    if data_table["Frequency"][i] >= data_table["Frequency"][i-1] and data_table["Frequency"][i] >= data_table["Frequency"][i+1]:
                        possible_freq_index.append([data_table["Frequency"][i], i])

                #if there is only one possilbe frequency then there's only one mode
                if len(possible_freq_index) == 0:
                    mode_string="No mode"

                elif len(set(data_table["Frequency"])) == 1:
                    mode_string="No mode, uniform"

                #if there is 2 peakes next to each other

                else:
                    modes=[]
                    for x in range(len(possible_freq_index)):

                        frequency = possible_freq_index[x][0]
                        index = possible_freq_index[x][1]
                        try:
                            class_modal = df.iloc[[index]]
                            class_frequency = data_table["Frequency"][index]
                            d1 = class_frequency - data_table["Frequency"][index-1]
                            d2 = class_frequency - data_table["Frequency"][index+1]
                            class_modal_lb = float(data_table["Class Boundries"][index].split(" → ")[0])

                            mode = round(((class_modal_lb + (d1/(d1+d2)) * c)), 2)
                            modes.append(mode)
                        except:
                            pass
                    modes=list(set(modes))
                    if len(modes) == 0:
                        mode_string="No mode"

                    mode_string=f"{len(modes)} modes, "
                    if len(modes) == 1:
                        mode_string = f"1 mode, {modes[0]}, unimodal."
                    elif len(modes) == 2:
                        mode_string+= f"{modes[0]} and {modes[1]}, bimodal."
                    else:
                        for mode in range(len(modes)-1):
                            mode_string+= str(modes[mode]) + ", "
                        mode_string+= f"and {modes[-1]}, multimodal."

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

            plt.title("Descending Cumulative Frequency Polygon (DCFP)")
            plt.xlabel("Class Boundreies")
            plt.ylabel("DCF")

            encoded = fig_to_base64(fig)
            dcfp = '<img src="data:image/png;base64, {}" , height="400" width="400" align="center">'.format(encoded.decode('utf-8'))

            #if the data is from a special case in the archive, it would redirict to a special page
            html_file = "table.html"
            if ques=="":
                pass
            elif ques in [25, 26, 27]:
                numbers_string=f"Chapter 1 Exercise {int(ques)}."
            else:
                html_file = "practice.html"

            possible_question_head = [histogram, polygon, acfp, dcfp]
            ques = 0
            return render_template(html_file,  tables=[HTML(df_show.to_html(classes='table table-striped table-dark', justify='center',index=False, table_id='table'))],
             titles=df.columns.values, numbers=numbers_string,
            mean = round(mean,2) , median = round(median,2), mode=mode_string,
            variance= round(variance,2), standerd_deviation=round(standerd_deviation, 2),
            Range = round(Range, 2), cv = round(cv, 2), histogram=HTML(histogram), polygon=HTML(polygon),
            acfp=HTML(acfp), dcfp=HTML(dcfp), head = HTML(possible_question_head[int(ques)]))

@app.route("/Archive/")
def archive():
    return render_template("archive.html")

@app.route("/Archive/Q25")
def q25():
    data = [3, 4, 4, 4, 4,
        7, 7, 7, 7, 7, 7, 7, 7, 7, 7,
        10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
        13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
        16, 16, 16, 16, 16, 16, 16, 16, 16, 17]

    return construct_table(data, 25)
@app.route("/Archive/Q26")
def q26():
    data = [1, 3, 3, 3, 3, 3, 3,
     8, 8, 8, 8, 8, 8, 8, 8, 8,
     13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13,
     18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 18,
     23, 23, 23, 23, 23, 23, 23, 25]

    return construct_table(data, 26)

@app.route("/Archive/Q27")
def q27():
    data = [5.5, 7.5, 7.5, 7.5, 7.5,
    12.5, 12.5, 12.5, 12.5, 12.5, 12.5, 12.5, 12.5, 12.5, 12.5, 12.5, 12.5, 12.5, 12.5, 12.5,
    17.5, 17.5, 17.5, 17.5, 17.5,
    22.5, 22.5, 22.5, 22.5, 22.5, 22.5, 22.5, 22.5, 22.5, 22.5,
    27.5, 27.5, 27.5, 27.5, 29.5]

    return construct_table(data, 27)

@app.route("/PracticePage")
def practicePage():
    return render_template("practicePage.html")

@app.route("/Practice/")
def practicing():
    data = []
    for x in range(50):
        data.append(randint(1, 40))

    temp = randint(1, 3)

    return construct_table(data, temp)

if __name__ == '__main__':
    app.debug=True
    app.run()
