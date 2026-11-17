from flask import Flask, render_template, request, redirect, url_for, flash, Response
import sqlite3, csv, io, os
from datetime import date
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "replace-this-before-deployment"
HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "trees.db")
UPLOADS = os.path.join(HERE, "static", "uploads")
os.makedirs(UPLOADS, exist_ok=True)

def connect():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    return c

def init_db():
    with connect() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS trees(
        id INTEGER PRIMARY KEY AUTOINCREMENT, species TEXT NOT NULL, location TEXT NOT NULL,
        planted_on TEXT NOT NULL, planted_by TEXT, status TEXT NOT NULL DEFAULT 'Healthy',
        notes TEXT, photo TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT, tree_id INTEGER NOT NULL, log_date TEXT NOT NULL,
        height_cm REAL, condition TEXT, notes TEXT, FOREIGN KEY(tree_id) REFERENCES trees(id))""")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/")
def home():
    q=request.args.get("q","").strip(); status=request.args.get("status","")
    sql="SELECT * FROM trees WHERE 1=1"; args=[]
    if q:
        sql+=" AND (species LIKE ? OR location LIKE ? OR planted_by LIKE ?)"; args += [f"%{q}%"]*3
    if status: sql+=" AND status=?"; args.append(status)
    with connect() as c:
        trees=c.execute(sql+" ORDER BY planted_on DESC, id DESC",args).fetchall()
        total=c.execute("SELECT COUNT(*) FROM trees").fetchone()[0]
        healthy=c.execute("SELECT COUNT(*) FROM trees WHERE status='Healthy'").fetchone()[0]
        care=c.execute("SELECT COUNT(*) FROM trees WHERE status='Needs care'").fetchone()[0]
    return render_template("home.html",trees=trees,q=q,status=status,total=total,healthy=healthy,care=care,
                           survival=round(healthy*100/total) if total else 0)

@app.route("/add",methods=["GET","POST"])
def add():
    if request.method=="POST":
        species=request.form.get("species","").strip()
        location=request.form.get("location","").strip()
        planted=request.form.get("planted_on","")
        if not species or not location or not planted:
            flash("Species, location and planting date are required."); return redirect(url_for("add"))
        photo=request.files.get("photo"); filename=None
        if photo and photo.filename:
            ext=photo.filename.rsplit(".",1)[-1].lower()
            if ext not in {"png","jpg","jpeg","webp"}:
                flash("Use a PNG, JPG or WEBP image."); return redirect(url_for("add"))
            filename=secure_filename(photo.filename.rsplit(".",1)[0])+"_"+os.urandom(3).hex()+"."+ext
            photo.save(os.path.join(UPLOADS,filename))
        with connect() as c:
            c.execute("INSERT INTO trees(species,location,planted_on,planted_by,status,notes,photo) VALUES(?,?,?,?,?,?,?)",
            (species,location,planted,request.form.get("planted_by",""),request.form.get("status","Healthy"),request.form.get("notes",""),filename))
        flash("Tree record saved."); return redirect(url_for("home"))
    return render_template("form.html",tree=None,today=date.today().isoformat())

@app.route("/tree/<int:tid>")
def detail(tid):
    with connect() as c:
        tree=c.execute("SELECT * FROM trees WHERE id=?",(tid,)).fetchone()
        logs=c.execute("SELECT * FROM logs WHERE tree_id=? ORDER BY log_date DESC",(tid,)).fetchall()
    if not tree: flash("Tree not found."); return redirect(url_for("home"))
    return render_template("detail.html",tree=tree,logs=logs,today=date.today().isoformat())

@app.route("/tree/<int:tid>/edit",methods=["GET","POST"])
def edit(tid):
    with connect() as c: tree=c.execute("SELECT * FROM trees WHERE id=?",(tid,)).fetchone()
    if not tree: return redirect(url_for("home"))
    if request.method=="POST":
        with connect() as c:
            c.execute("UPDATE trees SET species=?,location=?,planted_on=?,planted_by=?,status=?,notes=? WHERE id=?",
            (request.form["species"],request.form["location"],request.form["planted_on"],request.form.get("planted_by",""),request.form["status"],request.form.get("notes",""),tid))
        flash("Tree record updated."); return redirect(url_for("detail",tid=tid))
    return render_template("form.html",tree=tree,today=date.today().isoformat())

@app.route("/tree/<int:tid>/log",methods=["POST"])
def log(tid):
    with connect() as c:
        c.execute("INSERT INTO logs(tree_id,log_date,height_cm,condition,notes) VALUES(?,?,?,?,?)",
        (tid,request.form["log_date"],request.form.get("height_cm") or None,request.form.get("condition","Healthy"),request.form.get("notes","")))
    flash("Growth update recorded."); return redirect(url_for("detail",tid=tid))

@app.route("/tree/<int:tid>/delete",methods=["POST"])
def delete(tid):
    with connect() as c:
        c.execute("DELETE FROM logs WHERE tree_id=?",(tid,)); c.execute("DELETE FROM trees WHERE id=?",(tid,))
    flash("Tree record deleted."); return redirect(url_for("home"))

@app.route("/export")
def export():
    with connect() as c: rows=c.execute("SELECT id,species,location,planted_on,planted_by,status,notes FROM trees ORDER BY id").fetchall()
    out=io.StringIO(); w=csv.writer(out); w.writerow(["ID","Species","Location","Planting date","Planted by","Status","Notes"])
    w.writerows([tuple(r) for r in rows])
    return Response("\ufeff"+out.getvalue(),mimetype="text/csv",headers={"Content-Disposition":"attachment; filename=tree_records.csv"})

if __name__=="__main__":
    init_db(); app.run(debug=True)
