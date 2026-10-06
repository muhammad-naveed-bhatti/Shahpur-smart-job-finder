import streamlit as st
import pandas as pd
import requests
import re
from datetime import datetime

st.set_page_config(page_title="Shahpur Smart Job Finder", page_icon="💼", layout="wide")

DEFAULT_KEYWORDS = ["logistics","supply chain","warehouse","inventory","stores","procurement","fleet","transport","dispatch","aviation","material","operations","spares"]
CATEGORY_KEYWORDS = {
    "Logistics & Supply Chain": ["logistics","supply chain","logistic coordinator","supply specialist","material planning"],
    "Warehouse & Inventory": ["warehouse","inventory","storekeeper","stores","stock","material controller","warehouse supervisor"],
    "Procurement & Purchasing": ["procurement","purchasing","buyer","sourcing","vendor","purchase officer"],
    "Fleet, Transport & Dispatch": ["fleet","transport","dispatch","vehicle","driver operations","fleet coordinator"],
    "Aviation Logistics & Technical Spares": ["aviation","aircraft","mro","gse","technical stores","spares","aircraft material","aviation supply"],
    "Operations & Administration": ["operations","administration","admin","operations coordinator","operations manager"],
    "ERP / Logistics Systems": ["erp","wms","sap","oracle","logistics system","inventory system","warehouse management system"],
}
REGIONS = {
    "Pakistan": ["pakistan","lahore","sheikhupura","gujranwala","sialkot","karachi","islamabad","rawalpindi","faisalabad"],
    "GCC": ["saudi","riyadh","jeddah","dammam","uae","dubai","abu dhabi","qatar","doha","oman","muscat","bahrain","kuwait"],
    "Europe": ["europe","germany","netherlands","belgium","france","italy","spain","poland","romania","portugal","ireland","austria","sweden","denmark","norway"],
}

def detect_category(row):
    text=" ".join(str(row.get(k,"")) for k in ["Position","Tags","Description"]).lower()
    best="Other"; best_hits=0
    for cat, words in CATEGORY_KEYWORDS.items():
        hits=sum(1 for w in words if w in text)
        if hits>best_hits: best, best_hits=cat, hits
    return best

def detect_region(row):
    location=str(row.get("Location","")).lower()
    for region, words in REGIONS.items():
        if any(w in location for w in words): return region
    if str(row.get("Remote",""))=="Yes": return "Remote / Global"
    return "Other"

PRIORITY_PLACES = {"lahore":20,"sheikhupura":18,"gujranwala":16,"sialkot":16,"pakistan":12,"saudi":12,"riyadh":12,"jeddah":12,"uae":12,"dubai":12,"abu dhabi":12,"qatar":12,"doha":12,"oman":10,"bahrain":10,"kuwait":10,"germany":8,"europe":8}

def clean_html(s):
    return re.sub(r"<[^>]+>", " ", str(s or "")).replace("&nbsp;", " ")

@st.cache_data(ttl=1800)
def fetch_arbeitnow():
    r=requests.get("https://www.arbeitnow.com/api/job-board-api",timeout=25,headers={"User-Agent":"Shahpur-Smart-Job-Finder/1.0"})
    r.raise_for_status()
    jobs=[]
    for j in r.json().get("data",[]):
        jobs.append({"Source":"Arbeitnow","Company":j.get("company_name","Not stated"),"Position":j.get("title","Not stated"),"Location":j.get("location","Not stated"),"Remote":"Yes" if j.get("remote") else "No","URL":j.get("url",""),"Tags":", ".join(j.get("tags") or []),"Description":clean_html(j.get("description","")),"Date":datetime.fromtimestamp(j["created_at"]).strftime("%Y-%m-%d") if j.get("created_at") else "Not stated"})
    return jobs

@st.cache_data(ttl=1800)
def fetch_remoteok():
    r=requests.get("https://remoteok.com/api",timeout=25,headers={"User-Agent":"Shahpur-Smart-Job-Finder/1.0"})
    r.raise_for_status()
    jobs=[]
    for j in r.json():
        if not j.get("position"): continue
        jobs.append({"Source":"Remote OK","Company":j.get("company","Not stated"),"Position":j.get("position","Not stated"),"Location":j.get("location") or "Remote / Not stated","Remote":"Yes","URL":j.get("url",""),"Tags":", ".join(j.get("tags") or []),"Description":clean_html(j.get("description","")),"Date":j.get("date","Not stated")})
    return jobs

def score(row,terms,places):
    text=" ".join(str(row.get(k,"")) for k in ["Position","Company","Location","Tags","Description"]).lower()
    title=str(row.get("Position","")).lower(); location=str(row.get("Location","")).lower(); s=0
    for term in terms:
        t=term.lower().strip()
        if t and t in title: s+=25
        elif t and t in text: s+=10
    for p in places:
        p=p.lower().strip()
        if p and p in location: s+=PRIORITY_PLACES.get(p,8)
    return min(s,100)

st.title("💼 Shahpur Smart Job Finder")
st.caption("Logistics • Supply Chain • Aviation • Inventory • Procurement • Operations")
with st.sidebar:
    st.header("Search Preferences")
    keywords=st.text_area("Keywords (comma separated)",", ".join(DEFAULT_KEYWORDS))
    locations=st.text_area("Priority locations","Lahore, Sheikhupura, Gujranwala, Sialkot, Pakistan, Saudi, UAE, Qatar, Oman, Bahrain, Kuwait, Germany, Europe")
    min_score=st.slider("Minimum match score",0,100,10)
    category_filter=st.multiselect("Categories",["All Categories"]+list(CATEGORY_KEYWORDS.keys()),default=["All Categories"])
    region_filter=st.multiselect("Regions",["All Regions","Pakistan","GCC","Europe","Remote / Global","Other"],default=["All Regions"])
    remote_only=st.checkbox("Remote jobs only")
    run=st.button("🔎 Find Jobs",type="primary",use_container_width=True)

st.info("Sources: Arbeitnow + Remote OK public feeds. Always verify the vacancy and employer before applying.")
if run:
    terms=[x.strip() for x in keywords.split(",") if x.strip()]
    places=[x.strip() for x in locations.split(",") if x.strip()]
    all_jobs=[]; errors=[]
    for name,fn in [("Arbeitnow",fetch_arbeitnow),("Remote OK",fetch_remoteok)]:
        try: all_jobs.extend(fn())
        except Exception as e: errors.append(f"{name}: {e}")
    if not all_jobs:
        st.error("No jobs could be loaded. "+" | ".join(errors)); st.stop()
    df=pd.DataFrame(all_jobs)
    df["Category"]=df.apply(detect_category,axis=1)
    df["Region"]=df.apply(detect_region,axis=1)
    df["Match Score"]=df.apply(lambda r:score(r,terms,places),axis=1)
    df=df[df["Match Score"]>=min_score]
    if "All Categories" not in category_filter: df=df[df["Category"].isin(category_filter)]
    if "All Regions" not in region_filter: df=df[df["Region"].isin(region_filter)]
    if remote_only: df=df[df["Remote"]=="Yes"]
    df["_key"]=df["URL"].fillna(""); empty=df["_key"].eq("")
    df.loc[empty,"_key"]=df.loc[empty,"Company"].str.lower()+"|"+df.loc[empty,"Position"].str.lower()
    df=df.drop_duplicates("_key").drop(columns="_key").sort_values(["Match Score","Date"],ascending=[False,False])
    c1,c2,c3=st.columns(3); c1.metric("Matching jobs",len(df)); c2.metric("High matches (50+)",int((df["Match Score"]>=50).sum())); c3.metric("Sources active",df["Source"].nunique() if len(df) else 0)
    if errors: st.warning("Some sources failed: "+" | ".join(errors))
    if df.empty: st.warning("No matches. Lower the minimum score or broaden keywords/locations.")
    else:
        show=df[["Match Score","Category","Region","Date","Company","Position","Location","Remote","Source","URL"]]
        st.dataframe(show,use_container_width=True,hide_index=True,column_config={"URL":st.column_config.LinkColumn("Apply / View")})
        st.download_button("⬇️ Export results to CSV",show.to_csv(index=False).encode("utf-8-sig"),"Shahpur_Job_Results.csv","text/csv",use_container_width=True)
