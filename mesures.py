#-------------------------------------------------------------------------------
# Name:        mesure
# Purpose:     script de mesure de poids
# Author:      stephane kermorgant
# Created:     25/06/2019
#-------------------------------------------------------------------------------
#!/usr/bin/python

# ========================================================================
# import des modules
#=========================================================================
import sys
import os
import datetime
from datetime import datetime
import random
import mysql.connector
from mysql.connector import errorcode
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# ========================================================================
# ligne a decommenter sur raspberry
# ========================================================================
#import Adafruit_DHT
#os.chdir("/home/pi/Projet/essai/")

# ========================================================================
# definition de la classe ruche
# ========================================================================
class ruche:
    def __init__(self,nom,adresse,canal,gain,resolution,poids,t_ext,t_int,hum):
        self.nom = str(nom)
        self.adresse = adresse
        self.canal = canal
        self.gain = gain
        self.resolution = resolution
        self.poids = poids
        self.ext = t_ext
        self.int = t_int
        self.hum = hum

# ========================================================================
# definition des variables globales
# ========================================================================
nb_max = 5
deb_reg  = 0b10000000
lect_cont= 0b00010000
lect_seul= 0b00000000

horodatage = datetime.now()
time = horodatage.strftime("%H:%M:%S")
heure = horodatage.strftime("%H")
minute = horodatage.strftime("%M")
separateur = ";"
rien = ""
temp_ext = 25
temp_int = 20
poids = 42

# ========================================================================
# definition du tableau des balances
# ========================================================================
balance =(nb_max+1)*[ruche]
# premier MCP3424
balance[1]=ruche ("hydrogene",0x65,0b00000000,0b00000011,0b00001100,0,0,0,0)
balance[2]=ruche ("helium",0x65,0b00100000,0b00000011,0b00001100,0,0,0,0)
balance[3]=ruche ("lithium",0x65,0b01000000,0b00000011,0b00001100,0,0,0,0)
balance[4]=ruche ("beryllium",0x65,0b01100000,0b00000011,0b00001100,0,0,0,0)

# second MCP3424
balance[5]=ruche ("bore",0x66,0b00000000,0b00000011,0b00001100,0,0,0,0)

# ========================================================================
# liste des fonctions
# ========================================================================
def env_mail(date_jour,fic_log):
    Fromadd = "gite.kermorgant@gmail.com"
    Toadd = "kermorgant@gmail.com"
    Pass = "&AubiNKarinEStephanE&"
    message = MIMEMultipart()    
    message['From'] = Fromadd   
    message['To'] = Toadd
    message['Subject'] = "Mesures du " + str(date_jour)
    msg = "ci-joint les mesures du jour"
    message.attach(MIMEText(msg, 'plain'))
    ext = [".mes",".log",".err"]
    for i in ext:
        nom_fic = str(date_jour) + str(i)
        with open(nom_fic, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
        part.add_header('Content-Disposition', "piece; filename= %s" % nom_fic)
        message.attach(part)
    try:
        serveur = smtplib.SMTP('smtp.gmail.com', 587)
        serveur.starttls()
        texte= message.as_string()
        serveur.login(Fromadd, Pass)
        serveur.sendmail(Fromadd, Toadd, texte)
    except:
        print("erreur messagerie")
    else:
        print("mesures du jour transmises")
        serveur.quit()
        ecr_log(fic_log,15)

def ecr_ruche(boite,fic):
    reg_lec = str(horodatage) + separateur + str(boite.nom) + separateur + str(hex(boite.adresse)) + separateur + str(bin(boite.canal)) + separateur +str(bin(boite.gain)) + separateur + str(bin(boite.resolution)) + separateur + str(boite.poids) + separateur + str(boite.int) + separateur + str(boite.ext)+ separateur + str(boite.hum)
    fic.write(reg_lec+"\n")

def introduction (fic,heure):
    print (rien.ljust(100,'='))
    print ("= horodatage mesure        : " + heure)

def fic_mesures(horodatage):
    lib = horodatage.strftime("%Y-%m-%d")
    return(lib)

def ouv_fic(nom):
    try:
        fic_mes = open(nom + ".mes","a")
        fic_log = open(nom + ".log","a")
        fic_err = open(nom + ".err","a")
        print("= nom du fichier de mesure : " + nom + ".mes")
        print("= nom du fichier de log    : " + nom + ".log")
        print("= nom du fichier d'erreur  : " + nom + ".err")
        print (rien.ljust(100,'='))
        ecr_log(fic_log,0)
        ecr_log(fic_log,3)
        ecr_log(fic_log,2)
        return fic_mes,fic_log,fic_err;
    except IOError:
        print ("Impossible d'ouvrir : " + nom)

def conclusion(fic_log,fic_err,cnx):
    if int(heure) == 23:
        if int(minute) > 29:
            env_mail(nom,fic_log)
    ecr_log(fic_log,4)
    fic_log.close()
    fic_err.close()
    cnx.close()
    print (rien.ljust(100,'-'))
    sys.exit()

def recup_temp():
    rec_int = round(temp_int + random.uniform(-2,2),2)
    rec_ext = round(temp_ext + random.uniform(-4,4),2)
    return rec_int,rec_ext;

def recup_ext(fic_log):
    hum, temp = Adafruit_DHT.read_retry(11, 4)
    ecr_log(fic_log,16)
    return round(temp,2),int(hum);
    
def recup_poids():
    rec_poids = poids + random.randint(-4,4)
    return rec_poids;

def appel_mcp3424(balance,i):
    registre = deb_reg | balance.canal | balance.gain | balance.resolution | lect_seul
#    print("appel du MCP3424 pour balance : " + str(i) + " avec adresse : " + str(hex(balance.adresse)) + " et en parametre : " + str(bin(registre)))

def base_de_donnees(fic_err,fic_log,balance):
    try:
        cnx = mysql.connector.connect(user='pi', password='root',
                              host='jackandtenor.synology.me',
                              port='3307',
                              database='rucher')
    except:
        ecr_log(fic_log,1)
        print("erreur ouverture base ")
        sauv_reprise(fic_err,fic_log,balance)
        ecr_log(fic_log,4)
        fic_log.close()
        sys.exit()
    else:
        return(cnx)

def lire_tab_mes(cnx,fic):
    req = "select * from mesures"
    cursor = cnx_db.cursor()
    cursor.execute(req)
    records = cursor.fetchall()
    print("nb d'enregistrement(s) total dans " + nom + " est " +  str(cursor.rowcount))

def ecrire_tab_mes(cnx,balance):
    sel = """INSERT INTO `mesures` (`horodatage`, `nom`, `adresse`, `canal`, `gain`, `resolution`, `poids`, `interieur`, `exterieur`, `humidite`)"""
    val = "VALUES ('""" + str(horodatage)+"""', '"""+str(balance.nom)+"""', '"""+str(balance.adresse)+"""', '"""+str(balance.canal)+"""', '"""+str(balance.gain)+"""', '"""+str(balance.resolution)+"""', '"""+str(balance.poids)+"""', '"""+str(balance.int)+"""', '"""+str(balance.ext)+"""', '"""+str(balance.hum)+"""')"""
    req = sel + " " + val
    try:
        cursor = cnx.cursor()
        result = cursor.execute(req)
    except:
        print(str(req))
        print("erreur ecriture enregistrement")
    else:
        cnx.commit()

def sauv_reprise(fic_err,fic_log,boite):
    try:
        for i in range(1,nb_max+1):
            reg_err = str(horodatage) + separateur + str(boite[i].nom) + separateur + str(hex(boite[i].adresse)) + separateur + str(bin(boite[i].canal)) + separateur +str(bin(boite[i].gain)) + separateur + str(bin(boite[i].resolution)) + separateur + str(boite[i].poids) + separateur + str(boite[i].ext) + separateur + str(boite[i].int)
            fic_err.write(reg_err+"\n")
    except:
        ecr_log(fic_log,10)
        print("anomalie sauvegarde des mesures en erreur")
    else:
        ecr_log(fic_log,5)
        fic_err.close()

def ecr_log(fic_log,id_msg):
        reg_log ="message erreur : " + str(id_msg)
        if id_msg == 0:
            reg_log = "----------------------------------------------------------------------------"
        elif id_msg == 1:
            reg_log = str(horodatage) + " - anomalie ouverture base de donnee          : !!"
        elif id_msg == 2:
            reg_log = str(horodatage) + " - ouverture des fichiers                     : ok"
        elif id_msg == 3:
            reg_log = str(horodatage) + " - lancement des mesures"
        elif id_msg == 4:
            reg_log = str(horodatage) + " - fin des mesures"
        elif id_msg == 5:
            reg_log = str(horodatage) + " - sauvegarde mesures en erreur               : ok"
        elif id_msg == 6:
            reg_log = str(horodatage) + " - lecture temperature                        : ok"
        elif id_msg == 7:
            reg_log = str(horodatage) + " - lecture poids                              : ok"
        elif id_msg == 8:
            reg_log = str(horodatage) + " - sauvegarde en local des mesures            : ok"
        elif id_msg == 9:
            reg_log = str(horodatage) + " - sauvegarde sur base de donnees des mesures : ok"
        elif id_msg == 10:
            reg_log = str(horodatage) + " - anomalie sauvegarde des mesures en erreur  : !!"
        elif id_msg == 11:
            reg_log = str(horodatage) + " - anomalie lecture des temperatures          : !!"
        elif id_msg == 12:
            reg_log = str(horodatage) + " - anomalie lecture des poids                 : !!"
        elif id_msg == 13:
            reg_log = str(horodatage) + " - anomalie ecriture fichier des mesures      : !!"
        elif id_msg == 14:
            reg_log = str(horodatage) + " - anomalie sauvegarde base de donnee         : !!"
        elif id_msg == 15:
            reg_log = str(horodatage) + " - envoi du message recapitulatif             : ok"
        elif id_msg == 16:
            reg_log = str(horodatage) + " - lecture humidite + temperature exterieur   : ok"
        fic_log.write(reg_log+"\n")

# ===========================================================================
# programme principal
# ===========================================================================
nom=fic_mesures(horodatage)
introduction(nom,time)

# ouverture des fichiers
f_mes,f_log,f_err = ouv_fic(nom)

# mesures temperatures
try:
    humidite = 0
#    t_hum,humidite = recup_ext(f_log) # T + H exterieur en montage finale
    for i in range(1,nb_max+1):
        appel_mcp3424(balance[i],i)
        t_int,t_ext = recup_temp()
        balance[i].ext = t_ext
        balance[i].int = t_int
        balance[i].hum = humidite
        
except:
    ecr_log(f_log,11)
    print("erreur lecture temperature / humidite")
else:
    ecr_log(f_log,6)

# mesures de poids
try:
    for i in range(1,nb_max+1):
        t_poids = recup_poids()
        balance[i].poids = t_poids
except:
    ecr_log(f_log,12)
    print("erreur lecture temperature")
else:
    ecr_log(f_log,7)

# enregistrement fichier local
try:
    for i in range(1,nb_max+1):
        ecr_ruche(balance[i],f_mes)
    f_mes.close()
except:
    ecr_log(f_log,13)
    print("erreur ecriture du fichier de mesure")
else:
    ecr_log(f_log,8)

# sauvegarde base de donnees
cnx_db = base_de_donnees(f_err,f_log,balance)
try:
    for i in range(1,nb_max+1):
        ecrire_tab_mes(cnx_db,balance[i])
    lire_tab_mes(cnx_db,nom)
except:
    ecr_log(f_log,14)
    print("anomalie sauvegarde base de donnees")
else:
    ecr_log(f_log,9)
    conclusion(f_log,f_err,cnx_db)
