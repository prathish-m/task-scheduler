from flask import Flask,g,render_template,request
from colorama import Fore,Style
from datetime import datetime,timedelta
import sqlite3
import heapq

app=Flask(__name__,template_folder="templates",static_folder="static",static_url_path="/")
global_scheduledData=None

DATABASE = 'database/sqlite.db'
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

    
def init_database(fileName):
    fileName=fileName+'.db'
    with open('database/'+fileName,'a'):
        pass
    print('Database file created')

def init_schema():
    db = get_db()
    with app.open_resource('database/schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    print('Schema Initialised')

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

#TEMPLATE FILTERS

#completed
@app.template_filter("check_status")
def checkStatus(tasks,status):
    for task in tasks:
        if(task['status']==status):
            return True
    return False

#completed
@app.template_filter("convert_to_12_format")
def convertTo12Format(time):
    time_arr=time.split(":")
    ans=""
    hr=int(time_arr[0])
    if(hr == 0):
        ans="12"+":"+time_arr[1]+" AM"
    elif(hr<12):
        ans=time+" AM"
    elif(hr==12):
        ans=time+" PM"
    else:
        ans=str(hr-12)+":"+time_arr[1]+" PM"
    return ans

#ROUTES
#completed
@app.route("/")
def home():
    data=getScheduledTasks()
    print("data: ",data)
    return render_template("index.html",data=data)


#REST APIs

#complete
@app.route("/add-task",methods=['POST'])
def addTask():
    success={"message": "Success"}
    failure={"message": "Invalid Request"}
    data = request.get_json()
    if(not isinstance(data['name'],str) or len(data['name']) == 0):
        print("Invalid Name")
        return failure
    if(not isinstance(data['description'],str)):
        print("Invalid description")
        return failure
    if(not isinstance(data['starting_date'],str) or len(data['starting_date'])==0 or not isValidDateTimeFormat(data['starting_date'],"%Y-%m-%d")):
        print("Invalid starting_date")
        return failure
    if(not isinstance(data['starting_time'],str) or len(data['starting_time'])==0 or not isValidDateTimeFormat(data['starting_time'],"%H:%M")):
        print("Invalid starting_time")
        print(data['starting_time'])
        return failure
    dateTimeObj = datetime.strptime(data['starting_date']+" "+data['starting_time'],"%Y-%m-%d %H:%M")
    if(datetime.now()>=dateTimeObj):
        print("Less than current time")
        return failure
    if(dateTimeObj>datetime.now()+timedelta(days=365*5)):
        print("More than 5 years")
        return failure
    if(not isinstance(data['duration_unit'],str) or not (data['duration_unit'] == 'hrs' or data['duration_unit']=='mins')):
        print("Invalid duration_unit")
        return failure
    if(type(data['duration']) != int or (data['duration_unit'] == 'hrs' and data['duration']>24) or (data['duration_unit'] == 'mins' and data['duration']>24*60)):
        print("Invalid duration")
        print(data['duration'])
        print(data['duration_unit'])
        return failure
    
    if(type(data['priority']) != int or data['priority']<1 or data['priority']>5):
        print("Invalid priority")
        return failure
    try:
        get_db().cursor().execute("INSERT INTO TASKS(name,description,starting_date,starting_time,duration,duration_unit,priority) VALUES (?,?,?,?,?,?,?)",(data['name'],data['description'],data['starting_date'],data['starting_time'],data['duration'],data['duration_unit'],data['priority']))
        get_db().commit()
    except Exception as e:
        return {"Error Occured": str(e)}
    return success

@app.route("/get-task/<int:id>")
def getTask(id):
    return render_template("task.html",task=getTaskData(id))


#completed
@app.route("/get-expanded-task/<int:id>")
def getExpandedTask(id):
    return render_template("expanded_task.html",task=getTaskData(id))

#completed
@app.route("/mark-completed/<int:id>")
def markCompleted(id):
    msg=_updateTaskStatus(id,is_cancelled=0)  
    print(msg)                      
    return {"msg": msg}

#completed
@app.route("/mark-cancelled/<int:id>")
def markCancelled(id):
    msg=_updateTaskStatus(id,is_cancelled=1)
    print(msg)
    return {"msg": msg}

@app.route("/get-task-data/<int:id>")
def taskData(id):
    return getTaskData(id)

@app.route("/reschedule-task/<int:id>",methods=['POST'])
def rescheduleTask(id):
    updatedTaskData = request.get_json()
    msg="Success"
    failure={"message": "Invalid Request"}
    if(not _checkExist(id)):
        msg="Id does not exist"
    elif(not _checkCompletedOrCancelled(id)):
        msg="Task already marked as completed or cancelled"
    else:
        try:
            if(not isinstance(updatedTaskData['starting_date'],str) or not isValidDateTimeFormat(updatedTaskData['starting_date'],"%Y-%m-%d")):
                return failure
            if(not isinstance(updatedTaskData['starting_date'],str) or not isValidDateTimeFormat(updatedTaskData['starting_time'],"%H:%M")):
                return failure
            if(datetime.now()>=datetime.strptime(updatedTaskData['starting_date']+" "+updatedTaskData['starting_time'],"%Y-%m-%d %H:%M")):
                return failure

            if(not isinstance(updatedTaskData['duration_unit'],str) or not (updatedTaskData['duration_unit'] == 'hrs' or updatedTaskData['duration_unit']=='mins')):
                return failure
            if(type(updatedTaskData['duration']) != int or (updatedTaskData['duration_unit'] == 'hrs' and updatedTaskData['duration']>24) or (updatedTaskData['duration_unit'] == 'mins' and updatedTaskData['duration']>24*60)):
                return failure
            
            if(type(updatedTaskData['priority']) != int or updatedTaskData['priority']<1 or updatedTaskData['priority']>5):
                return failure
            get_db().cursor().execute("UPDATE TASKS SET starting_date=?,starting_time=?,duration=?,duration_unit=?,priority=?  where id=?",(updatedTaskData['starting_date'],updatedTaskData['starting_time'],updatedTaskData['duration'],updatedTaskData['duration_unit'],updatedTaskData['priority'],id))
            get_db().commit()
        except Exception as e:
            msg="Database Error: "+str(e)                                
    return {"message": msg}



#Custom functions

def _setSchedules(data):
    global global_scheduledData
    global_scheduledData=data

def getTaskData(id):
    if global_scheduledData is None:
        return ""
    for data in global_scheduledData:
        if(data['id'] == id):
            return data
    return ""


def isValidDateTimeFormat(value,pattern):
    try:
        datetime.strptime(value,pattern)
        return True
    except ValueError:
        return False


#update status to a task as completed or cancelled
def _updateTaskStatus(id,is_cancelled):
    msg="Success"
    if(not _checkExist(id)):
        msg="Id does not exist"
    elif(not _checkCompletedOrCancelled(id)):
        msg="Task already marked as completed or cancelled"
    else:
        current_datetime=datetime.now()
        cancelled_date=current_datetime.strftime("%Y-%m-%d")
        cancelled_time=current_datetime.strftime("%H:%M")
        try:
            get_db().cursor().execute("UPDATE TASKS SET is_cancelled=?,completed_date=?,completed_time=? where id=?",(is_cancelled,cancelled_date,cancelled_time,id))
            get_db().commit()
        except Exception as e:
            msg="Database Error: "+str(e)                                
    return {"message": msg}

#Check whether ID exist in database
#completed
def _checkExist(id):
    print("Inside _checkExist")
    db_data=get_db().cursor().execute("SELECT * FROM TASKS WHERE id=?",(id,)).fetchall()
    print(f"db data: {db_data}")
    return (len(db_data) == 1)

#completed
def _checkCompletedOrCancelled(id):
    print("Inside _checkCompletedOrCancelled")
    db_data=get_db().cursor().execute("SELECT * FROM TASKS WHERE id=? AND completed_date IS NULL AND completed_time IS NULL",(id,)).fetchall()
    print(f"db data: {db_data}")
    return len(db_data) == 1

#To conver single tuple to corresponding object
def _packObject(data):
    obj={}
    obj['id'],obj['name'],obj['description'],obj['starting_date'],obj['starting_time'],obj['duration'],obj['duration_unit'],obj['priority'],obj['completed_date'],obj['completed_time'],obj['is_cancelled']=data
    return obj

#To convert all tuples to corresponding objects
def _packObjects(datas):
    packed_data=[]
    for data in datas:
        packed_data.append(_packObject(data))
    return packed_data

def _getDateGroups(datas):
    date_groups={}
    for data in datas:
        date=""
        if(data['completed_date'] is None):
            date=data['actual_starting_date']
        else:
           date=data['completed_date']
        if(date not in date_groups.keys()):
            date_groups[date]=[]
        date_groups[date].append(data)
    return date_groups


def _setDue(datas):
    for data in datas:
        duration_min=0
        if(data['duration_unit'] == 'hrs'):
            duration_min=data['duration']*60
        else:
            duration_min=data['duration']
        current_time=datetime.now().replace(second=0,microsecond=0)
        start_datetime = datetime.strptime(data['actual_starting_date']+" "+data['actual_starting_time'],"%Y-%m-%d %H:%M")
        completion_datetime=start_datetime+timedelta(minutes=duration_min)
        time_difference_sec = (completion_datetime - current_time).total_seconds()
        data['isDue']=(time_difference_sec<=0)
    return datas

def _setStatus(datas):
    for data in datas:
        if(data['completed_time'] is None):
            data['status']='pending'
        else:
            if(data['is_cancelled'] == 1):
                data['status']='cancelled'
            else:
                data['status'] = 'completed'
        del data['is_cancelled']
    return datas

def _toArrayDateGroups(date_groups):
    arr=[]
    for key in date_groups.keys():
        arr.append({
            "date": key,
            "tasks": date_groups[key]
        })
    return arr

def __dateComparator(o):
    return datetime.strptime(o['date'],"%Y-%m-%d").timestamp()

def __timeComparator(o):
    if(o['status'] == 'pending'):
        return datetime.strptime(o['actual_starting_date']+" "+o['actual_starting_time'],"%Y-%m-%d %H:%M").timestamp()
    return -datetime.strptime(o['completed_date']+" "+o['completed_time'],"%Y-%m-%d %H:%M").timestamp()

def _classifyPendingAndNotPendingData(datas):
    p_data=[]
    o_data=[]
    for data in datas:
        if(data['status']=='pending'):
            p_data.append(data)
        else:
            o_data.append(data)
    return (p_data,o_data)

def getScheduledTasks():
    def __format(arr):
        print("Date Epochs: ")
        for a in arr:
            print(f"\tStarting Datetime: {datetime.fromtimestamp(a[0]).strftime('%Y-%m-%d %H:%M')} Ending Datetime: {datetime.fromtimestamp(a[1]).strftime('%Y-%m-%d %H:%M')}")

    db_data=get_db().cursor().execute("SELECT * FROM TASKS").fetchall()
    packed_data = _packObjects(db_data)
    packed_data=_setStatus(packed_data) ##set and status
    pending_data,not_pending_data = _classifyPendingAndNotPendingData(packed_data)
    date_epochs=[]
    heap = [(-task["priority"],-task["id"], task) for task in pending_data]
    heapq.heapify(heap)
    scheduled_pending_dates=[]
    print(f"No of pending tasks: {len(heap)}")
    print("")
    while(len(heap)>0):

        pri,id,ob=heapq.heappop(heap)
        print(f"ID: {ob['id']}\nPriority: {ob['priority']}")
        print(f"Starting Datetime: {ob['starting_date']} {ob['starting_time']}")
        print(f"Duration: {ob['duration']} {ob['duration_unit']}")
        starting_datetime_obj  = datetime.strptime(ob['starting_date']+" "+ob['starting_time'],"%Y-%m-%d %H:%M")
        __format(date_epochs)
        starting_epoch = int(starting_datetime_obj.timestamp())
        duration_mins = ob['duration']*(1+59*(ob['duration_unit']=='hrs'))
        ending_datetime_obj = starting_datetime_obj+timedelta(minutes=duration_mins)
        ending_epoch= int(ending_datetime_obj.timestamp())
        cp=-1 #collision point
        for i in range(len(date_epochs)):
            ep=date_epochs[i]
            if(starting_epoch < ep[1] and (ending_epoch > ep[0])):
                cp=i
                break
        ob['isRescheduled']=bool(cp!=-1)
        if(cp == -1):
            print("No collision")
            print(f"Actual Starting time: {ob['starting_date']} {ob['starting_time']}")
            print(f"Actual ending time: {datetime.fromtimestamp(ending_epoch).strftime('%Y-%m-%d %H:%M')}")
            ob['actual_starting_time']=ob['starting_time']
            ob['actual_starting_date']=ob['starting_date']
            flag=False
            for i in reversed(range(0,len(date_epochs))):
                if(date_epochs[i][1]<starting_epoch):
                    date_epochs.insert(i+1,[starting_epoch,ending_epoch])
                    flag=True
                    break
            if(not flag):
                date_epochs.insert(0,[starting_epoch,ending_epoch])
        else:
            print(f"Collision in Starting datetime: {datetime.fromtimestamp(date_epochs[cp][0]).strftime("%Y-%m-%d %H:%M")} and Ending datetime: {datetime.fromtimestamp(date_epochs[cp][1]).strftime("%Y-%m-%d %H:%M")} at index {cp}")
            least_to_right = -1
            least_to_left = -1
            duration_secs = duration_mins*60
            for i in range(cp,len(date_epochs)-1):
                time_diff = date_epochs[i+1][0]-date_epochs[i][1]
                if(time_diff >=  duration_secs):
                    least_to_right=i+1
                    break
            if(least_to_right == -1):
                least_to_right=len(date_epochs)
            for i in reversed(range(1,cp+1)):
                time_diff=date_epochs[i][0] - date_epochs[i-1][1]
                if(time_diff >= duration_secs*60):
                    least_to_left=i
                    break
            if(least_to_left == -1):
                least_to_left=0
            print(f"least to left: {least_to_left}, least to right: {least_to_right}")
            isValidLeft = ((date_epochs[least_to_left][0]-duration_secs - int(datetime.now().timestamp())) > 60)

            if(not isValidLeft or date_epochs[least_to_right-1][1] - starting_epoch <= starting_epoch - date_epochs[least_to_left][0]+ duration_secs ):
                print(f"inserting at {least_to_right}")
                actual_starting_time = date_epochs[least_to_right-1][1]
                actual_ending_time = date_epochs[least_to_right-1][1]+duration_secs
                actual_starting_datetime = datetime.fromtimestamp(actual_starting_time).strftime('%Y-%m-%d %H:%M').split(' ')
                ob['actual_starting_time']=actual_starting_datetime[1]
                ob['actual_starting_date']=actual_starting_datetime[0]
                actual_ending_datetime = datetime.fromtimestamp(actual_ending_time).strftime('%Y-%m-%d %H:%M').split(' ')
                print(f"Rescheduled to {ob['actual_starting_date']} {ob['actual_starting_time']}\nEnding Datetime: {actual_ending_datetime[0]} {actual_ending_datetime[1]}")
                date_epochs.insert(least_to_right,[actual_starting_time,actual_ending_time])
            else:
                print(f"inserting before {least_to_left}")
                actual_ending_time = date_epochs[least_to_left][0]
                actual_starting_time = date_epochs[least_to_left][0]-duration_secs
                actual_starting_datetime = datetime.fromtimestamp(actual_starting_time).strftime('%Y-%m-%d %H:%M').split(' ')
                actual_ending_datetime = datetime.fromtimestamp(actual_ending_time).strftime('%Y-%m-%d %H:%M').split(' ')
                ob['actual_starting_time']=actual_starting_datetime[1]
                ob['actual_starting_date']=actual_starting_datetime[0]
                print(f"Rescheduled to \nStarting Datetime: {ob['actual_starting_date']} {ob['actual_starting_time']}\nEnding Datetime: {actual_ending_datetime[0]} {actual_ending_datetime[1]}")
                date_epochs.insert(least_to_left,[actual_starting_time,actual_ending_time])
        scheduled_pending_dates.append(ob)  
        print()
    scheduled_pending_dates=_setDue(scheduled_pending_dates)
    scheduled_pending_dates.extend(not_pending_data)
    _setSchedules(scheduled_pending_dates)
    date_groups = _toArrayDateGroups(_getDateGroups(scheduled_pending_dates))
    sorted_date_groups = sorted(date_groups,key=__dateComparator)
    for dg in sorted_date_groups:
        dg['tasks']=sorted(dg['tasks'],key=__timeComparator)
    # print(sorted_date_groups)
    return sorted_date_groups



if __name__ == "__main__":
    with app.app_context():
        print(Fore.GREEN)
        init_database("sqlite")
        init_schema()
        getScheduledTasks()
        print(Style.RESET_ALL)
    app.run(host='0.0.0.0',port=8000,debug=True)