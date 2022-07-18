from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory, send_file
# from pdf2docx import Converter
from docx2pdf import convert
from pdf2jpg import pdf2jpg
from pdf2image import convert_from_path
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
import sys
import img2pdf
from PIL import Image
import aspose.words as aw
# import pdf_compressor
from PyPDF2 import PdfMerger
import PyPDF2
import pikepdf

# set Flask scheduler configuration values
class Config:
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "Europe/Berlin"


app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.db') 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '@pdftools'
db = SQLAlchemy(app)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DOWNLOAD_FOLDER = 'downloads/'
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER



# tasks model 
class Tasks(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True,autoincrement=True)
    folder=db.Column(db.String(255))
    filename = db.Column(db.String(255))
    time_added = db.Column(db.String(255))
    

    def __init__(self,folder, filename, time_added ):
        self.folder = folder
        self.filename  = filename 
        self.time_added = time_added

    def __repr__(self):
        return '<Task %r>' % self.filename 

# flask scheduler
app.config.from_object(Config())
# initialize scheduler
scheduler = APScheduler()
# if you don't wanna use a config, you can set options here:
# scheduler.api_enabled = True
scheduler.init_app(app)

# Scheduler for sending mails to inform user about their bids
@scheduler.task('interval', id='do_job_1', seconds=120, misfire_grace_time=9)
def job1():    
    tasks = Tasks.query.all()
    for i in tasks:
        print(i.id)
        try:
            os.remove(os.path.join(DOWNLOAD_FOLDER)+i.filename)
            os.remove(os.path.join(UPLOAD_FOLDER)+i.filename)
        except Exception as e:
            print(str(e))
        db.session.delete (i)
        db.session.commit() 
        print("deleted!")
scheduler.start()

@app.route("/")
def index():
    return render_template("index.html")
    
@app.route('/download/<string:filename>')
def download(filename):
    print(filename)
    document_path = os.path.join(DOWNLOAD_FOLDER)+filename
    try:
        file = open(document_path, 'r')
    except:
        file= None
    if file:
        assign_task_to_remove_file(filename=filename)
        return send_file(os.path.join(DOWNLOAD_FOLDER)+filename, attachment_filename=filename)
    else:
        return "File Expired!"


def assign_task_to_remove_file(filename):
    # os.path.join(DOWNLOAD_FOLDER)
    # os.remove(os.path.join(DOWNLOAD_FOLDER)+filename)
    task = Tasks(folder="downloads",filename=filename,time_added=datetime.strptime(datetime.now().strftime('%Y-%m-%d %H'), '%Y-%m-%d %H') )
    db.session.add(task)
    db.session.commit() 
    print(filename," assigned task to for deleting!")


# @app.route("/pdf-to-doc",methods=['GET','POST'])
# def pdf_to_doc():
#     if request.method == "POST":
#         file = request.files['fileList[]']
#         filename = secure_filename(file.filename)
#         file.save(os.path.join(UPLOAD_FOLDER, filename))
#         pdf_file = "uploads/"+filename
#         filename2 = filename.replace(".pdf",".docx")
#         docx_file = "downloads/"+filename2

#         # convert pdf to docx
#         cv = Converter(pdf_file)
#         cv.convert(docx_file)     
#         cv.close()
#         response = "/download/"+filename2
#         return response

#     return render_template("pdf-to-doc-converter.html")

@app.route("/pdf-to-doc",methods=['GET','POST'])
def pdf_to_doc():
    if request.method == "POST":
        files = []        
        i  = 0
        while (True):
            try:
                name = "fileList[]"+str(i)
                if request.files[name]:
                    file = request.files[name]
                    files.append(file)
                    i = i+1
                else:
                    break
            except Exception as e:
                    break
        filenames = []
        for i in files:
            filename = secure_filename(i.filename)
            filenames.append(filename)
            i.save((os.path.join(UPLOAD_FOLDER, filename)))

        # convert pdf to docx
        responses = []
        for  i in filenames:
            # pdf_file = "uploads/"+i
            filename2 = i.replace(".pdf",".docx")
            # docx_file = "downloads/"+filename2
            # cv = Converter(pdf_file)
            # cv.convert(docx_file)     
            # cv.close()

            doc = aw.Document("uploads/"+i)
            doc.save("downloads/"+filename2)
            responses.append(filename2)
        response = "/downloads/"+str(responses)
        return str(responses)

    return render_template("pdf-to-doc-converter.html")

@app.route("/doc-to-pdf",methods=['GET','POST'])
def doc_to_pdf():
    if request.method == "POST":
        files = []  
        i  = 0
        while (True):
            try:
                name = "fileList[]"+str(i)
                if request.files[name]:
                    file = request.files[name]
                    files.append(file)
                    i = i+1
                else:
                    break
            except Exception as e:
                    break
        filenames = []
        for i in files:
            filename = secure_filename(i.filename)
            filenames.append(filename)
            i.save((os.path.join(UPLOAD_FOLDER, filename)))
        
        responses = []
        for i in filenames:
        
            # doc_file = "uploads/"+filename
            filename2 = i.replace(".docx",".pdf")
            # # pdf_file = "downloads/"+filename2
            # docx_file = 'uploads/'+i
            # pdf_file = 'downloads/'+filename2
            # convert(docx_file, pdf_file)

            doc = aw.Document("uploads/"+i)
            doc.save("downloads/"+filename2)

            responses.append(filename2)
        # response = "download/"+filename2
        return str(responses)
        print('done')
        

    return render_template("doc-to-pdf-converter.html")



@app.route("/pdf-to-jpg",methods=['GET','POST'])
def pdf_to_jpg():
    if request.method == "POST":
        files = []  
        i  = 0
        while (True):
            try:
                name = "fileList[]"+str(i)
                if request.files[name]:
                    file = request.files[name]
                    files.append(file)
                    i = i+1
                else:
                    break
            except Exception as e:
                    break
        filenames = []
        for i in files:
            filename = secure_filename(i.filename)
            filenames.append(filename)
            i.save((os.path.join(UPLOAD_FOLDER, filename)))
        
        responses = []
        for i in filenames:

            # pages = convert_from_path(os.path.join(UPLOAD_FOLDER, i), 500)
            
            filename2 = i.replace(".pdf",".jpg")
        
            # for page in pages:
            #     page.save(os.path.join(DOWNLOAD_FOLDER,filename2), 'JPEG')
            doc = aw.Document("uploads/"+i)
                      
            for page in range(0, doc.page_count):
                extractedPage = doc.extract_pages(page, 1)
                extractedPage.save(f"downloads/{page + 1}"+filename2)
                responses.append(f"{page+1}"+filename2)
        return str(responses)

    return render_template("pdf-to-jpg-converter.html")

@app.route("/jpg-to-pdf",methods=['GET','POST'])
def jpg_to_pdf():
    if request.method == "POST":
        files = []  
        i  = 0
        while (True):
            try:
                name = "fileList[]"+str(i)
                if request.files[name]:
                    file = request.files[name]
                    files.append(file)
                    i = i+1
                else:
                    break
            except Exception as e:
                    break
        filenames = []
        for i in files:
            filename = secure_filename(i.filename)
            i.save((os.path.join(UPLOAD_FOLDER, filename)))
            filenames.append(filename)
        
        responses = []
        for i in filenames:
            filename2 = i.replace(".jpg",".pdf")
            # img_path = os.path.join(UPLOAD_FOLDER, i)
            img_path = "uploads/"+i
            # pdf_path = os.path.join(DOWNLOAD_FOLDER, filename2)
            pdf_path = "downloads/"+filename2
            print(img_path)
            print(pdf_path)
            image = Image.open(img_path)
            pdf_bytes = img2pdf.convert(image.filename)
            file = open(pdf_path, "wb")
            file.write(pdf_bytes)
            image.close()
            file.close()
            responses.append(filename2)
        return str(responses)

    return render_template("jpg-to-pdf-converter.html")

@app.route("/pdf-to-png",methods=['GET','POST'])
def pdf_to_png():
    if request.method == "POST":
        files = []  
        i  = 0
        while (True):
            try:
                name = "fileList[]"+str(i)
                if request.files[name]:
                    file = request.files[name]
                    files.append(file)
                    i = i+1
                else:
                    break
            except Exception as e:
                    break
        filenames = []
        for i in files:
            filename = secure_filename(i.filename)
            i.save((os.path.join(UPLOAD_FOLDER, filename)))
            filenames.append(filename)
        
        responses = []
        for i in filenames:
            
            filename2 = i.replace(".pdf",".png")
        
            doc = aw.Document("uploads/"+i)
          
            for page in range(0, doc.page_count):
                extractedPage = doc.extract_pages(page, 1)
                extractedPage.save(f"downloads/{page + 1}"+filename2)
                responses.append(f"{page+1}"+filename2)
        return str(responses)

    return render_template("pdf-to-png-converter.html")

@app.route("/png-to-pdf",methods=['GET','POST'])
def png_to_pdf():
    if request.method == "POST":
        files = []  
        i  = 0
        while (True):
            try:
                name = "fileList[]"+str(i)
                if request.files[name]:
                    file = request.files[name]
                    files.append(file)
                    i = i+1
                else:
                    break
            except Exception as e:
                    break
        filenames = []
        for i in files:
            filename = secure_filename(i.filename)
            i.save((os.path.join(UPLOAD_FOLDER, filename)))
            filenames.append(filename)
        
        responses = []
        for i in filenames:  
            doc = aw.Document()
            builder = aw.DocumentBuilder(doc)

            builder.insert_image("uploads/"+i)

            filename2 = i.replace(".png",".pdf")

            doc.save("downloads/"+filename2)     
            responses.append(filename2)
        return str(responses)

    return render_template("png-to-pdf-converter.html")

@app.route("/pdf-compressor",methods=['GET','POST'])
def pdf_compressor():
    if request.method == "POST":
        file = request.files['fileList[]']
        filename = secure_filename(file.filename)
        file.save((os.path.join(UPLOAD_FOLDER, filename))) 
        img_path = "uploads/"+filename 
        output_pdf = "downloads/"+filename
        reader = PyPDF2.PdfReader(img_path)
        writer = PyPDF2.PdfWriter()

        for page in reader.pages:
            page.compress_content_streams()
            writer.add_page(page)

        with open(output_pdf, "wb") as f:
            writer.write(f)
        output_pdf = "downloads/"+filename

        response = "/download/"+filename
        return response
    return render_template("pdf-compressor.html")


# @app.route("/pdf-compressor",methods=['GET','POST'])
# def pdf_compressor():
#     if request.method == "POST":
#         file = request.files['fileList[]']
#         filename = secure_filename(file.filename)
#         # file.save((os.path.join(UPLOAD_FOLDER, filename))) 

#         file.save((os.path.join(DOWNLOAD_FOLDER, filename))) 
        
#         response = "/download/"+filename
#         return response
#     return render_template("pdf-compressor.html")

@app.route("/crop-pdf",methods=['GET','POST'])
def crop_pdf():
    from PyPDF2 import PdfWriter, PdfReader
    if request.method == "POST":
        files = []        
        i  = 0
        while (True):
            try:
                name = "fileList[]"+str(i)
                if request.files[name]:
                    file = request.files[name]
                    files.append(file)
                    i = i+1
                else:
                    break
            except Exception as e:
                    break
        filenames = []
        for i in files:
            filename = secure_filename(i.filename)
            filenames.append(filename)
            i.save((os.path.join(UPLOAD_FOLDER, filename)))

        # convert pdf to docx
        responses = []


        import PyPDF2 # version 1.26.0
        for  i in filenames:
            img_path = "uploads/"+i
            filename2 = "cropped-"+str(i)
            reader = PdfReader(img_path)
            writer = PdfWriter()
            for i in range(len(reader.pages)):
                # add page 3 from reader, but crop it to half size:
                page = reader.pages[i]
                page.mediabox.upper_right = (
                    page.mediabox.right - 50,
                    page.mediabox.top - 50,
                )
                page.mediabox.lower_left = (
                    page.mediabox.left + 50,
                    page.mediabox.bottom + 50,
                )
                writer.add_page(page)

            # write to document-output.pdf
            output_pdf ="downloads/"+filename2
            with open(output_pdf, "wb") as fp:
                writer.write(fp)
            # output_pdf ="static/PyPDF2-output.pdf"
             
            responses.append(filename2)
        
        return str(responses)

    return render_template("crop-pdf.html")

# @app.route("/crop-pdf",methods=['GET','POST'])
# def crop_pdf():
#     if request.method == "POST":
#         files = []        
#         i  = 0
#         while (True):
#             try:
#                 name = "fileList[]"+str(i)
#                 if request.files[name]:
#                     file = request.files[name]
#                     files.append(file)
#                     i = i+1
#                 else:
#                     break
#             except Exception as e:
#                     break
#         filenames = []
#         for i in files:
#             filename = secure_filename(i.filename)
#             filenames.append(filename)
#             i.save((os.path.join(UPLOAD_FOLDER, filename)))

#         # convert pdf to docx
#         responses = []


#         from PyPDF2 import PdfWriter, PdfReader
#         for  i in filenames:

#             reader = PdfReader('uploads/'+i) 
#             writer = PdfWriter()

#             for page in reader.pages:
#               page.cropbox.upper_left = (100,200)
#               page.cropbox.lower_right = (300,400)
#               writer.add_page(page) 

#             filename2 = "cropped-"+i
              
#             with open('downloads/'+filename2,'wb') as fp:
#                 writer.write(fp) 
#             responses.append(filename2)
        
#         return str(responses)

#     return render_template("crop-pdf.html")

@app.route("/rotate-pdf",methods=['GET','POST'])
def rotate_pdf():
    if request.method == "POST":
        files = []        
        i  = 0
        while (True):
            try:
                name = "fileList[]"+str(i)
                if request.files[name]:
                    file = request.files[name]
                    files.append(file)
                    i = i+1
                else:
                    break
            except Exception as e:
                    break
        filenames = []
        for i in files:
            filename = secure_filename(i.filename)
            filenames.append(filename)
            i.save((os.path.join(UPLOAD_FOLDER, filename)))

        # convert pdf to docx
        responses = []
        rotate_angle = request.form.get("rotateAngle")
        for i in filenames:
            # file = request.files['fileList[]']
            # rotate_angle = request.form.get("rotateAngle")
            # file.save((os.path.join(UPLOAD_FOLDER, i)))  
            pdf_in = open('uploads/'+i, 'rb')
            pdf_reader = PyPDF2.PdfFileReader(pdf_in)
            pdf_writer = PyPDF2.PdfFileWriter()
            for pagenum in range(pdf_reader.numPages):
                page = pdf_reader.getPage(pagenum)
                page.rotateClockwise(int(rotate_angle))
                pdf_writer.addPage(page)
            filename2 = str(rotate_angle)+"-rotated-"+i
            pdf_out = open('downloads/'+filename2, 'wb')
            pdf_writer.write(pdf_out)
            pdf_out.close()
            pdf_in.close()
            response = "/download/"+filename2             
            responses.append(filename2)
        return str(responses) 

    return render_template("rotate-pdf.html")

# @app.route("/rotate-pdf",methods=['GET','POST'])
# def rotate_pdf():
#     if request.method == "POST":
#         file = request.files['fileList[]']
#         rotate_angle = request.form.get("rotateAngle")
#         filename = secure_filename(file.filename)
#         file.save((os.path.join(UPLOAD_FOLDER, filename)))  
#         pdf_in = open('uploads/'+filename, 'rb')
#         pdf_reader = PyPDF2.PdfFileReader(pdf_in)
#         pdf_writer = PyPDF2.PdfFileWriter()
#         for pagenum in range(pdf_reader.numPages):
#             page = pdf_reader.getPage(pagenum)
#             page.rotateClockwise(int(rotate_angle))
#             pdf_writer.addPage(page)
#         filename2 = str(rotate_angle)+"-rotated-"+filename
#         pdf_out = open('downloads/'+filename2, 'wb')
#         pdf_writer.write(pdf_out)
#         pdf_out.close()
#         pdf_in.close()
#         response = "/download/"+filename2
#         return response

#     return render_template("rotate-pdf.html")

@app.route("/unlock-pdf",methods=['GET','POST'])
def unlock_pdf():
    if request.method == "POST":
        file = request.files['fileList[]']
        filename = secure_filename(file.filename)
        file.save((os.path.join(UPLOAD_FOLDER, filename)))  

        pdf = pikepdf.open('uploads/'+filename)
        filename2 = "unlocked-"+filename
        pdf.save('downloads/'+filename2)

        response = "/download/"+filename2
        return response

    return render_template("unlock-pdf.html")

@app.route("/combine-pdf",methods=['GET','POST'])
def combine_pdf():
    if request.method == "POST":
        files = []        
        i  = 0
        while (True):
            try:
                name = "fileList[]"+str(i)
                print(name)
                if request.files[name]:
                    file = request.files[name]
                    files.append(file)
                    i = i+1
                else:
                    break
            except Exception as e:
                    break
        print("files is: ")
        print(files)
        filenames = []
        for i in files:
            filename = secure_filename(i.filename)
            filenames.append(filename)
            i.save((os.path.join(UPLOAD_FOLDER, filename)))  

        merger = PdfMerger()

        # for pdf in pdfs:
        for pdf in filenames:
            merger.append("uploads/"+pdf)
            # merger.append(pdf)
        filename2 = "result.pdf"
        merger.write("downloads/"+filename2)
        merger.close()

        response = "/download/"+filename2
        return response

    return render_template("combine-pdf.html")





if __name__=='__main__':
    app.run(debug=True)
    # app.run(debug=True,use_reloader=False)