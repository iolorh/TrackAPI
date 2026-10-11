from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fastapi.responses import RedirectResponse
import feedbackTable
from connection import get_db
import sqlite3
from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import bcrypt
from dotenv import load_dotenv
import os
import apisTable
import httpx
import snapshotsTable
import json
from deepdiff import DeepDiff
import changesTable
import accountsTable
from fastapi.staticfiles import StaticFiles
import datetime
from pathlib import Path
import resend
from zoneinfo import ZoneInfo
from datetime import timezone



app = FastAPI()
load_dotenv()
app.add_middleware(SessionMiddleware, secret_key=os.environ["SECRET_KEY"])
app.mount("/static", StaticFiles(directory="static"), name="static")
resend.api_key = os.getenv("RESEND_API_KEY")
templates = Jinja2Templates(directory = "templates")

def hash_function(password):
    return bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())


def uk_time(timestamp):

    dt = timestamp.replace(tzinfo=timezone.utc)

    return dt.astimezone(ZoneInfo("Europe/London"))

async def send_change_email(c,api_id,change_type,description,breaking):
    api_name = apisTable.get_name_by_id(c,api_id)
    user_id = apisTable.get_user_id_by_api_id(c,api_id)
    user_email = accountsTable.get_email_by_id(c,user_id)
    if breaking == 0:
        breaking = "Non-breaking"
    elif breaking == 1:
        breaking = "Breaking"
    elif breaking == 2:
        breaking ="Potentially breaking"

    try:
        await resend.Emails.send_async({
            "from": "TrackAPI <no-reply@trackapi.uk>",
            "to": [user_email],
            "subject": f"{api_name} - {breaking} change detected" ,
            "html": f"<p>{description}</p><p>Change type: {change_type}</p> <a href='https://trackapi.uk' target='_blank'>https://trackapi.uk</a>",
        })

    except Exception as e:
        print(f"Failed to send email: {e}")    

async def handle_item_added(change,api_id,c, old_spec, new_spec,old_snapshot_id,conn):
    path = change.path(output_format="list")
    if path[0] == "paths" and len(path) == 2:
        if len(change.t2) > 1:
            amount = 0
            for method in change.t2:
                description = f"{method} {path[-1]} - Endpoint added"
                breaking = 0
                changesTable.add_change(c,api_id,"Item added",description,breaking, old_spec, new_spec,"->".join(map(str, change.path(output_format="list"))),old_snapshot_id,conn)
                await send_change_email(c,api_id,"Item added",description,breaking)
                amount += 1
            return amount - 1
        else:
            description = f"{next(iter(change.t2))} {path[-1]} - Endpoint added"
        breaking = 0
    elif path[0] =="paths" and len(path) == 3:
        description = f"{path[-1]} {path[-2]} - Endpoint added"
        breaking = 0
    elif path[-2] == "properties":
        description = f"Schema property {path[-1]} added to {path[-3]}"
        breaking = 0
    elif path[-2] == "responses":
        description = f"response {path[-1]} Added to {path[-3]} {path[-4]}"
        breaking = 0
    else:
        x = path.pop()
        description = f"{x} added to {"->".join(map(str, path))}"
        breaking = 2
    changesTable.add_change(c,api_id,"Item added",description,breaking, old_spec, new_spec,"->".join(map(str, change.path(output_format="list"))),old_snapshot_id,conn)
    await send_change_email(c,api_id,"Item added",description,breaking)

async def handle_item_removed(change,api_id,c, old_spec, new_spec,old_snapshot_id,conn):
    path = change.path(output_format="list")
    if path[0] == "paths" and len(path) == 2:
        if len(change.t1) > 1:
            amount = 0
            for method in change.t1:
                description = f"{method} {path[-1]} - Endpoint removed"
                breaking = 1
                changesTable.add_change(c,api_id,"Item removed",description,breaking,old_spec, new_spec,"->".join(map(str, change.path(output_format="list"))),old_snapshot_id,conn)
                await send_change_email(c,api_id,"Item added",description,breaking)
                amount += 1
            return amount - 1
        else:
            description = f"{next(iter(change.t1))} {path[-1]} - Endpoint removed"
        breaking = 1
    elif path[0] =="paths" and len(path) == 3:
        description = f"{path[-1]} {path[-2]} - Endpoint removed"
        breaking = 1
    elif path[-2] == "responses":
        description = f"response {path[-1]} removed from {path[-3]} {path[-4]}"
        breaking = 1
    elif path[-2] == "properties":
        description=f"Schema property {path[-1]} removed from {path[-3]}"
        breaking = 2
    elif path[-2] == "content":
        if path[-3] == "requestBody":
            description = f"Content type {path[-1]} removed from request body of {path[2]} {path[1]}"
        else:
            description = f"Content type {path[-1]} removed from response {path[-3]} in {path[2]} {path[1]}"
        breaking = 1
    else:
        x = path.pop()
        description = f"{x} removed from {"->".join(map(str, path))}"
        breaking = 2
    changesTable.add_change(c,api_id,"Item removed",description,breaking,old_spec, new_spec,"->".join(map(str, change.path(output_format="list"))),old_snapshot_id,conn)
    await send_change_email(c,api_id,"Item added",description,breaking)

async def handle_type_change(change,api_id,c,old_spec, new_spec,old_snapshot_id,conn):
    description = f"{change.path(output_format = "list")[-1]} changed from {type(change.t1).__name__} (value {change.t1}) to {type(change.t2).__name__} (value {change.t2})"
    breaking = 2
    changesTable.add_change(c,api_id,"Type changed",description,breaking,old_spec, new_spec,"->".join(map(str, change.path(output_format="list"))),old_snapshot_id,conn)
    await send_change_email(c,api_id,"Item added",description,breaking)

async def handle_value_change(change,api_id,c,old_spec, new_spec,old_snapshot_id,conn):
    path = change.path(output_format="list")
    if path[0] == "paths" and len(path) == 2:
        if len(change.t2) > 1:
            amount = 0
            for method in change.t2:
                description = f"{method} {path[-1]} - Endpoint added"
                breaking = 0
                changesTable.add_change(c,api_id,"Item added",description,breaking, old_spec, new_spec,"->".join(map(str, change.path(output_format="list"))),old_snapshot_id,conn)
                await send_change_email(c,api_id,"Item added",description,breaking)
                amount += 1
        else:
            description = f"{next(iter(change.t2))} {path[-1]} - Endpoint added"
            breaking = 0
            changesTable.add_change(c,api_id,"Item added",description,breaking, old_spec, new_spec,"->".join(map(str, change.path(output_format="list"))),old_snapshot_id,conn)
            await send_change_email(c,api_id,"Item added",description,breaking)

        if len(change.t1) > 1:
            amount = 0
            for method in change.t1:
                description = f"{method} {path[-1]} - Endpoint removed"
                breaking = 1
                changesTable.add_change(c,api_id,"Item removed",description,breaking,old_spec, new_spec,"->".join(map(str, change.path(output_format="list"))),old_snapshot_id,conn)
                await send_change_email(c,api_id,"Item added",description,breaking)
                amount += 1
        else:
            description = f"{next(iter(change.t1))} {path[-1]} - Endpoint removed"
            breaking = 1
            changesTable.add_change(c,api_id,"Item removed",description,breaking,old_spec, new_spec,"->".join(map(str, change.path(output_format="list"))),old_snapshot_id,conn)
            await send_change_email(c,api_id,"Item added",description,breaking)
        return amount
    elif path[-1] == "type":
        if path[-2] == "schema":
            description = f"Schema type for {change.up.up.t1["name"]} in {path[2]} {path[1]} changed from {change.t1} to {change.t2}"
        elif path[-3] =="anyOf":
            description = f"Schema type for {change.up.up.up.up.t1["name"]} in {path[2]} {path[1]} changed from {change.t1} to {change.t2}"
        else:
            description = f"Schema type for {path[-2]} in {path[2]} changed from {change.t1} to {change.t2}"
        breaking = 1
    elif path[-1] == "required" and path[-3] == "parameters" and change.t1 == False and change.t2 == True:
        description = f"{change.up.t1["name"]} parameter in {path[2]} {path[1]} is now required"
        breaking = 1
    else:
        x = path.pop()
        description = f"{x} value in {"->".join(map(str, path))} changed from {change.t1} to {change.t2}"
        breaking = 2
    changesTable.add_change(c,api_id,"Value changed",description,breaking,old_spec, new_spec,"->".join(map(str, change.path(output_format="list"))),old_snapshot_id,conn)
    await send_change_email(c,api_id,"Item added",description,breaking)

async def handle_iterable_item_added(change,api_id,c,old_spec, new_spec,old_snapshot_id,conn):
    path = change.path(output_format="list")
    if path[-2] == "required":
        description = f"{change.t2} added to required list for {path[-3]} schema"
        breaking = 1
    elif path[-2] == "enum":
        if path[-3] == "schema":
            description = f"{change.t2} added to  enum list for {change.up.up.up.t1["name"]} parameter in {path[2]} {path[1]}"
        else:
            description = f"{change.t2} added to enum list for {change.up.up.up.up.up.t1["name"]} paramater in {path[2]} {path[1]}"
        breaking = 0
    else:
        path.pop()
        x = path.pop()
        description = f"{change.t2} added to {x} list in {"->".join(map(str, path))}"
        breaking = 2
    changesTable.add_change(c,api_id,"List item added",description,breaking,old_spec, new_spec,"->".join(map(str, change.path(output_format="list"))),old_snapshot_id,conn)
    await send_change_email(c,api_id,"Item added",description,breaking)

async def handle_iterable_item_removed(change,api_id,c,old_spec, new_spec,old_snapshot_id,conn):
    path = change.path(output_format="list")
    if path[-2] == "enum":
        if path[-3] == "schema":
            description = f"{change.t1} removed from enum list for {change.up.up.upt1["name"]} parameter in {path[2]} {path[1]}"
        else:
            description = f"{change.t1} removed from enum list for {change.up.up.up.up.up["name"]} paramater in {path[2]} {path[1]}"
        breaking = 1
    elif path[-2] == "required":
        description = f"{change.t1} removed from required list for {path[-3]} schema"
        breaking = 0
    else:
        path.pop()
        x = path.pop()
        description = f"{change.t1} removed from {x} list in {"->".join(map(str, path))}"
        breaking = 2 
    changesTable.add_change(c,api_id,"List item removed",description,breaking,old_spec, new_spec,"->".join(map(str, change.path(output_format="list"))),old_snapshot_id,conn)
    await send_change_email(c,api_id,"Item added",description,breaking)

handlers = {
    "dictionary_item_added":handle_item_added,
    "dictionary_item_removed":handle_item_removed,
    "type_changes":handle_type_change,
    "values_changed":handle_value_change,
    "iterable_item_added":handle_iterable_item_added,
    "iterable_item_removed":handle_iterable_item_removed
}


async def run_api_check(c,api_id,conn):
    url = apisTable.get_url(c,api_id)
    new_spec = await fetch_spec(url)
    old_spec = json.loads(snapshotsTable.get_latest_spec(0,c,api_id))
    old_snapshot_id = snapshotsTable.get_latest_spec(1,c,api_id)
    diff = DeepDiff(old_spec, new_spec, view = "tree", verbose_level = 2)
    if diff:
        snapshotsTable.create_snapshot(c,json.dumps(new_spec, indent = 2),api_id,conn)
        amount_of_changes = 0
        for change_type, changes in diff.items():
            for change in changes:
                amount_of_changes += 1
                handler = handlers.get(change_type)
                if handler:
                    amount = await handler(change, api_id, c, json.dumps(old_spec, indent = 2), json.dumps(new_spec, indent = 2),old_snapshot_id,conn)
                    if amount:
                        amount_of_changes += amount
        if amount_of_changes == 1:
            message = "1 new change since last check"
        else:
            message = f"{amount_of_changes} new changes since last check"
    else:
        apisTable.update_last_checked(c,api_id,conn)
        message = "No new changes since last check"
    return message


async def fetch_spec(url):
    try:
        async with httpx.AsyncClient(
            headers={
                "User-Agent": "TrackAPI",
                "Accept": "application/json, application/*+json"
            },
            follow_redirects=True,
            timeout=10.0
        ) as client:

            response = await client.get(url)
            response.raise_for_status()

            spec = response.json()

            if not isinstance(spec, dict):
                return None

            if "openapi" not in spec and "swagger" not in spec:
                return None

            return spec

    except (httpx.HTTPError, ValueError):
        return None

@app.get("/signin-page")
def signin(request : Request, message : str | None = None):
    id = request.session.get("account_id")
    if id:
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse(
        request = request,
        name="signinpage.html",
        context={"message":message}
    )


@app.post("/signin-page/login")
def login(request : Request, email : str = Form(), password : str = Form(), c: sqlite3.Connection = Depends(get_db)):
    exists,id = accountsTable.account_exists(c,email,password)
    if exists:
        request.session["account_id"] = id
        return RedirectResponse("/dashboard",status_code = 303)
    return RedirectResponse(url="/signin-page?message=Account doesn't exist",status_code = 303)
    
@app.post("/signin-page/register")
def register(request : Request, email : str = Form(), password : str = Form(), c: sqlite3.Connection = Depends(get_db)):
    exists = accountsTable.email_exists(c,email)
    if not exists:
        id = accountsTable.create_account(c,email,hash_function(password))
        request.session["account_id"] = id
        return RedirectResponse("/dashboard",status_code = 303)
    return RedirectResponse(url="/signin-page?message=Email already registered",status_code = 303)


@app.get("/")
def home(request : Request, feedback : str | None = None):
    id = request.session.get("account_id")
    if id :
        return RedirectResponse("/dashboard", status_code = 303)
    return templates.TemplateResponse(
        request = request,
        name = "home.html",
        context = {"email": feedback}
    )

@app.get("/dashboard")
def dashboard(request : Request, c: sqlite3.Connection = Depends(get_db), message : str | None = None):
    id = request.session.get("account_id")
    breakingAmount = 0
    if id:
        email = accountsTable.get_email_by_id(c,id)
        apis = apisTable.get_apis_by_id(c, id)
        changes = changesTable.get_changes_by_id(c, id)
        for change in changes:
            if change["breaking"] == 1:
                change["breaking"] = "🔴"
                breakingAmount += 1
            elif change["breaking"] == 0:
                change["breaking"] = "🟢"
            else:
                change["breaking"] = "🟠"
            x = datetime.datetime.fromisoformat(change["detected_at"])
            x = uk_time(x)
            change["detected_at"] = {
                "month": x.strftime("%b"),
                "day": x.strftime("%d"),
                "time": f"{x.strftime("%H")}:{x.strftime("%M")}"
            }

            change["api_name"] = apisTable.get_name_by_id(c,change["api_id"])

        for api in apis:
            y = datetime.datetime.fromisoformat(api["last_checked"])
            y = uk_time(y)
            api["last_checked"] = {
                "month": y.strftime("%b"),
                "day": y.strftime("%d"),
                "time": f"{y.strftime("%H")}:{y.strftime("%M")}"
            }
        apis_amount = len(apis)
        changes_amount = len(changes)


    else:
        changes,email,apis = None,None,None
        apis_amount = 0
        changes_amount = 0

    if breakingAmount == 0:
        health = 100
    else:
        health = 100-breakingAmount*100 // len(changes)

    
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"apis" : apis,
                 "changes": changes,
                 "email" : email,
                 "message" : message,
                 "apisAmount": apis_amount,
                 "changesAmount": changes_amount,
                 "breakingAmount": breakingAmount,
                 "status": f"{health}%"}
    )


@app.get("/allapis")
def allapis(request : Request, c: sqlite3.Connection = Depends(get_db), apinumber : int | None = None):
    id = request.session.get("account_id")
    if id:
        email = accountsTable.get_email_by_id(c,id)
        apis = apisTable.get_apis_by_id(c, id)
        if apinumber:
            spec = snapshotsTable.get_latest_spec(0,c,apinumber)
            apiname = apisTable.get_name_by_id(c,apinumber)
            apiurl = apisTable.get_url(c,apinumber)
        else:
            spec = ""
            apiname = ""
            apiurl = "Select an API to view it's most recent spec 🡭"
        for api in apis:
            y = datetime.datetime.fromisoformat(api["last_checked"])
            y = uk_time(y)
            api["last_checked"] = {
                "month": y.strftime("%b"),
                "day": y.strftime("%d"),
                "time": f"{y.strftime("%H")}:{y.strftime("%M")}"
            }
        apis_amount = len(apis) 
    else:
        apis_amount = 0
        email = None
        apis = None
        spec = ""
        apiname = ""  
        apiurl = ""     
    return templates.TemplateResponse(
        request=request,
        name="apis.html",
        context={"apis": apis,
                 "email" : email,
                 "spec" : spec,
                 "apiname" : apiname,
                 "apiurl": apiurl,
                 "apisAmount": apis_amount
                 }
    )


@app.get("/allchanges")
def allchanges(request: Request, c: sqlite3.Connection = Depends(get_db), apichoice : str | None = None, breakingchoice : str | None = None, changenumber : int | None = None):
    id = request.session.get("account_id")
    if id:
        email = accountsTable.get_email_by_id(c,id)
        changes = changesTable.get_changes_by_id(c,id)
        apis = apisTable.get_apis_by_id(c, id)
        breakingAmount = 0
        apiselected = apichoice
        breakingselected = breakingchoice

        if changenumber:
            api_name = apisTable.get_api_name_by_change_id(c,changenumber)
            path = changesTable.get_path_by_change_id(c,changenumber)
            old_spec,new_spec = changesTable.get_specs_by_change_id(c,changenumber)
            old_spec = json.loads(old_spec)
            new_spec = json.loads(new_spec)
            for i in path.split("->"):
                if type(old_spec).__name__ == "dict":
                    old_spec = old_spec.get(i)
                    new_spec = new_spec.get(i)
                else:
                    break
            
            old_spec = json.dumps(old_spec, indent= 2)
            new_spec = json.dumps(new_spec, indent = 2)
            selected_change = changenumber
            old_spec_date = uk_time(datetime.datetime.fromisoformat(changesTable.get_old_spec_date_by_change_id(c,changenumber)))
            new_spec_date = uk_time(datetime.datetime.fromisoformat(changesTable.get_detected_at_by_change_id(c,changenumber)))
            oldDate = {
                "month": old_spec_date.strftime("%b"),
                "day": old_spec_date.strftime("%d"),
                "time": f"{old_spec_date.strftime("%H")}:{old_spec_date.strftime("%M")}"
            }
            newDate = {
                "month": new_spec_date.strftime("%b"),
                "day": new_spec_date.strftime("%d"),
                "time": f"{new_spec_date.strftime("%H")}:{new_spec_date.strftime("%M")}"
            }
        else:
            old_spec,new_spec = "",""
            selected_change = None
            path = ""
            oldDate = None
            newDate = None
            api_name = ""
        print(path)
        if apichoice == "All":
            changes = changesTable.get_changes_by_id(c,id)
        elif apichoice == None:
            changes = changesTable.get_changes_by_id(c,id)
        else:
            changes = changesTable.get_changes_by_api_name(c,apichoice)

        for change in changes:
            if change["breaking"] == 1:
                change["breaking"] = "🔴 [ BREAKING ]"
                breakingAmount += 1
            elif change["breaking"] == 0:
                change["breaking"] = "🟢 [ NON-BREAKING ] "
            else:
                change["breaking"] = "🟠 [ POTENTIALLY BREAKING ]"
            x = datetime.datetime.fromisoformat(change["detected_at"])
            x = uk_time(x)
            change["detected_at"] = {
                "month": x.strftime("%b"),
                "day": x.strftime("%d"),
                "time": f"{x.strftime("%H")}:{x.strftime("%M")}"
            }

            change["api_name"] = apisTable.get_name_by_id(c,change["api_id"])

        if breakingchoice != None and breakingchoice != "All":
            newchanges = [change for change in changes if change["breaking"][0] == breakingchoice]
        else:
            newchanges = changes
        changes_amount = len(newchanges)

            
    else:
        email = None
        changes_amount = 0
        newchanges = None
        apis = None
        apiselected = None
        breakingselected = None
        old_spec = None
        new_spec = None
        selected_change=path=newDate=oldDate=None
        api_name = ""
        path=""
        
    return templates.TemplateResponse(
        request = request,
        name="changes.html",
        context={
            "email":email,
            "changesAmount": changes_amount,
            "changes": newchanges,
            "apis": apis,
            "apiselected": apiselected,
            "breakingselected": breakingselected,
            "oldspec" : old_spec,
            "newspec" : new_spec,
            "selectedChange" : selected_change,
            "path": path,
            "newDate": newDate,
            "oldDate": oldDate,
            "apiname": api_name
        }
    )


@app.get("/allchanges/seediff/{change_id}")
def seediff(change_id : int, c: sqlite3.Connection = Depends(get_db)):
    return RedirectResponse(url=f"/allchanges?changenumber={change_id}", status_code = 303)
    


@app.get("/allapis/seespec/{api_id}")
def seespec(api_id: int, c: sqlite3.Connection = Depends(get_db)):
    return RedirectResponse(url=f"/allapis?apinumber={api_id}", status_code = 303)
    

@app.post("/logout")
def logout(request : Request):
    request.session["account_id"] = None
    return RedirectResponse("/dashboard", status_code = 303)

@app.post("/add-api")
async def add_api(request : Request, url : str = Form(),name : str = Form(), c: sqlite3.Connection = Depends(get_db)):
    id = request.session.get("account_id")
    if not id:
        return RedirectResponse("/signin-page", status_code = 303)
    spec = json.dumps(await fetch_spec(url), indent = 2)
    if spec != "null":
        api_id = apisTable.add_api(c,name,url,id)
        snapshotsTable.create_snapshot(c,spec,api_id,c)
    return RedirectResponse("/dashboard", status_code = 303)

@app.post("/apis/{api_id}/check")
async def check(api_id: int, c: sqlite3.Connection = Depends(get_db)):
    message = await run_api_check(c,api_id,c)
    return RedirectResponse(url=f"/dashboard?message={message}", status_code = 303)


@app.post("/apis/{api_id}/delete")
def delete(api_id: int, c: sqlite3.Connection = Depends(get_db)):
    apisTable.delete_api(c,api_id)
    return RedirectResponse("/dashboard", status_code = 303)



@app.post("/allchanges/dropdownfilter/")
def dropdownfilter(request : Request, apichoice : str = Form(), breakingchoice : str = Form()):
    id = request.session.get("account_id")
    if not id:
        return RedirectResponse("/signin-page", status_code = 303)
    return RedirectResponse(url=f"/allchanges?apichoice={apichoice}&breakingchoice={breakingchoice}", status_code = 303)



@app.post("/home/feedback")
def feedback(email : str = Form()):
    return RedirectResponse(url=f"/home?feedback={email}", status_code = 303)

@app.post("/home/feedback/send/{email}")
def sendfeedback(email : str, message : str = Form(), c: sqlite3.Connection = Depends(get_db)):
    feedbackTable.add_feedback(c,email,message)
    return RedirectResponse("/", status_code = 303)


@app.get("/robots.txt")
def robots():
    return FileResponse("static/robots.txt")

@app.get("/sitemap.xml")
def sitemap():
    return FileResponse(
        "static/sitemap.xml",
        media_type="application/xml"
    )
