from flask import Flask,render_template,request,redirect,url_for,flash,send_from_directory,send_file
from werkzeug.utils import secure_filename
from werkzeug import SharedDataMiddleware
from google.cloud import vision
import os,io

app = Flask(__name__)
folder = "uploads/"
UPLOAD_FOLDER = '.'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.add_url_rule('/uploads/<filename>','uploaded_file',build_only=True)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
        '/uploads':  app.config['UPLOAD_FOLDER']
        })

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

@app.route('/')
def home():
    return render_template('home.html')

def allowed_file(filename):
        return '.' in filename and \
                           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload',methods=['GET','POST'])
def upload():
    print(request.files)
    string = ""
    if request.method == 'POST':
        if 'file' not in request.files:
            print('No file part')
        else:
            uploaded_file = request.files['file']
            if uploaded_file.filename == '':
                print('No selected file')
            
            if uploaded_file and allowed_file(uploaded_file.filename):
                print('Recieved file')
                filename = secure_filename(uploaded_file.filename)
                uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
                string = detect_text(uploaded_file.filename)
                os.rename(uploaded_file.filename,folder+uploaded_file.filename)
    return render_template('home.html',string_variable=string)
    
@app.route('/uploads/<filename>')
def uploaded_filename(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                                           filename)
def detect_text(path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../account-key.json"
    client = vision.ImageAnnotatorClient()
    string = ""
    with io.open(path,'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    response = client.document_text_detection(image=image)

    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            print('\nBlock confidence: {}\n'.format(block.confidence))
            for paragraph in block.paragraphs:
                print('Paragraph confidence: {}'.format(paragraph.confidence))
                for word in paragraph.words:
                    word_text = ' '.join([symbol.text for symbol in word.symbols])
                    print('Word text : {} (confidence {})'.format(word_text, word.confidence))
                    string += ' '
                    for symbol in word.symbols:
                        string += symbol.text
                        print('\tSymbol : {} (confidence: {})'.format(symbol.text, symbol.confidence))

    f = open('img_to_txt.txt','w')
    f.write(string)
    f.close()
    return string

if __name__ == "__main__":
    app.run()
