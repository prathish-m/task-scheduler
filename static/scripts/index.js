const addTaskBtn = document.getElementById("add-task")
const newTaskForm = document.getElementById("new-task")
const rescheduleTaskForm = document.getElementById("reschedule-task")
const newTaskDialog = document.getElementById("new-task-dlg")
const rescheduleTaskDialog = document.getElementById("reschedule-task-dlg")
const priority=document.getElementById("priority")
const priorityInput = document.getElementById("priority-val")
const tasksContainer = document.getElementById("tasks-container-wrapper")
const closeAddFormBtn = document.getElementById("close-add-form-btn")
const closeRescheduleFormBtn = document.getElementById("close-reschedule-form-btn")

// Reschedule form data binding
const rescheduleId = document.getElementById("reschedule-id")
const rescheduleName = document.getElementById("reschedule-name")
const rescheduleDescription = document.getElementById("reschedule-description")
const rescheduleDate = document.getElementById("reschedule-date")
const rescheduleHour = document.getElementById("reschedule-hour")
const rescheduleMin = document.getElementById("reschedule-min")
const rescheduleTimePeriod = document.getElementById("reschedule-time-period")
const rescheduleDuration = document.getElementById("reschedule-duration")
const rescheduleDurationUnit = document.getElementById("reschedule-duration-unit")
const reschedulePriority = document.getElementById("reschedule-priority")


priorityInput.value=priority.value


//custom functions
function parseDate(date){
    dateArr = date.split('-')
    if(dateArr[1].length === 1) dateArr[1]='0'+dateArr[1]
    if(dateArr[2].length === 1) dateArr[2]='0'+dateArr[2]
    return dateArr.join('-')
}

function convertTo24Format(hour,min,timePeriod){
    if(hour === '12' && timePeriod === 'am') hour='0'
    if(timePeriod === 'pm' && parseInt(hour)!=12) hour=(parseInt(hour)+12).toString()
    if(hour.length == 1) hour='0'+hour
    if(min.length == 1) min='0'+min
    return hour+":"+min
}

function getHour(hour){
    if(hour == 0) return 12
    if(hour > 12) return hour-12
    return hour
}


function isValidInteger(duration){
    for(let it=0;it<duration.length;it++){
        if(duration[it]<'0' || duration[it]>'9') return false;
    }
    return true;
}

//event listeners
newTaskForm.addEventListener("submit",(e)=>{
    e.preventDefault()
    let formData = new FormData(newTaskForm)
    const newTaskData = Object.fromEntries(formData)
    let parsedNewTaskData = {}
    if(newTaskData['name'].length === 0) {
        alert("Name cannot be empty")
        return
    }
    if(newTaskData['date'].length === 0) {
        alert("Date cannot be empty")
        return
    }

    if(newTaskData['hour'].length === 0) {
        alert("Time(Hour) cannot be empty")
        return
    }
    if(newTaskData['min'].length === 0) {
        alert("Time(Minutes) cannot be empty")
        return
    }
    if(newTaskData['duration'].length === 0) {
        alert("Duration cannot be empty")
        return
    }
    if(!isValidInteger(newTaskData['hour']) || !isValidInteger(newTaskData['min'])){
        alert("Time is invalid")
        return
    }
    let newFormHour = parseInt(newTaskData['hour']),newFormMin=parseInt(newTaskData['min'])
    if(newFormHour<1 || newFormHour>12){
        alert("Time is invalid")
        return
    }
    if(newFormMin<0 || newFormMin>59){
        alert("Time is invalid")
        return
    }
    if(isNaN(new Date(newTaskData['date']+"T"+convertTo24Format(newTaskData['hour'],newTaskData['min'],newTaskData['time-period'])))){
        alert("Invalid Date")
        return 
    }
    let newFormDateTime = new Date(newTaskData['date']+"T"+convertTo24Format(newTaskData['hour'],newTaskData['min'],newTaskData['time-period']))
    let currentDateTime = Date.now()+1000*60
    if(currentDateTime > newFormDateTime){
        alert("Task time must be atleast 1 min more than current time")
        return
    }
    let maxYears = 5;
    if(newFormDateTime > (currentDateTime+ 1000*60*60*24*365*maxYears)){
        alert("Cannot scheduled a task after 5 years")
        return 
    }

    if(!isValidInteger(newTaskData['duration'])){
        alert("Not a valid duration")
        return
    }

    if(String(newTaskData['duration-unit']).localeCompare('mins') === 0 && newTaskData['duration']>24*60){
        alert(`Maximum minutes is: ${24*60}`)
        return
    }
    if(String(newTaskData['duration-unit']).localeCompare('hrs') === 0 && newTaskData['duration']>24){
        alert(`Maximum hours is: 24`)
        return
    }

    parsedNewTaskData['name']=newTaskData['name']
    parsedNewTaskData['description']=newTaskData['description']
    parsedNewTaskData['starting_date']=newTaskData['date']
    parsedNewTaskData['starting_time']=convertTo24Format(newTaskData['hour'],newTaskData['min'],newTaskData['time-period'])
    parsedNewTaskData['duration']=parseInt(newTaskData['duration'])
    parsedNewTaskData['duration_unit']=newTaskData['duration-unit']
    parsedNewTaskData['priority']=parseInt(newTaskData['priority'])
    fetch("/add-task",{
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(parsedNewTaskData)
    }).then(async (data)=>{
        msg = await data.json()
        alert(msg['message'])
    }).catch((err)=>{
        alert("Error happened: "+err)
    }).finally(()=>location.reload(true))
    
})

rescheduleTaskForm.addEventListener("submit",(e)=>{

    e.preventDefault()
    let formData = new FormData(rescheduleTaskForm)
    const newRescheduledData = Object.fromEntries(formData)
    let parsedRescheduledTaskData = {}
    if(newRescheduledData['date'].length === 0) {
        alert("Date cannot be empty")
        return
    }

    if(newRescheduledData['hour'].length === 0) {
        alert("Time(Hour) cannot be empty")
        return
    }
    if(newRescheduledData['min'].length === 0) {
        alert("Time(Minutes) cannot be empty")
        return
    }
    if(newRescheduledData['duration'].length === 0) {
        alert("Duration cannot be empty")
        return
    }
    if(!isValidInteger(newRescheduledData['hour']) || !isValidInteger(newRescheduledData['min'])){
        alert("Time is invalid")
        return
    }
    let rescheduleFormHour = parseInt(newRescheduledData['hour']),rescheduleFormMin=parseInt(newRescheduledData['min'])

    if(rescheduleFormHour<1 || rescheduleFormHour>12){
        alert("Time is invalid")
        return
    }
    if(rescheduleFormMin<0 || rescheduleFormMin>59){
        alert("Time is invalid")
        return
    }
    if(isNaN(new Date(newRescheduledData['date']+"T"+convertTo24Format(newRescheduledData['hour'],newRescheduledData['min'],newRescheduledData['time-period'])))){
        alert("Invalid Date")
        return 
    }
    let rescheduleFormDateTime = new Date(newRescheduledData['date']+"T"+convertTo24Format(newRescheduledData['hour'],newRescheduledData['min'],newRescheduledData['time-period']))
    let currentDateTime = Date.now()+1000*60
    if(currentDateTime > rescheduleFormDateTime){
        alert("Task time must be atleast 1 min more than current time")
        return
    }
    let maxYears = 5
    if(rescheduleFormDateTime > (currentDateTime+ 1000*60*60*24*365*maxYears)){
        alert("Cannot scheduled a task after 5 years")
        return 
    }

    if(!isValidInteger(newRescheduledData['duration'])){
        alert("Not a valid duration")
        return
    }
    
    if(String(newRescheduledData['duration-unit']).localeCompare('mins')===0 && parseInt(newRescheduledData['duration'])>24*60){
        alert(`Maximum minutes is: ${24*60}`)
        return
    }
    if(String(newRescheduledData['duration-unit']).localeCompare('hrs')===0 && parseInt(newRescheduledData['duration'])>24){
        alert("Maximum hours is: 24")
        return
    }

    parsedRescheduledTaskData['starting_date']=newRescheduledData['date']
    parsedRescheduledTaskData['starting_time']=convertTo24Format(newRescheduledData['hour'],newRescheduledData['min'],newRescheduledData['time-period'])
    parsedRescheduledTaskData['duration']=parseInt(newRescheduledData['duration'])
    parsedRescheduledTaskData['duration_unit']=newRescheduledData['duration-unit']
    parsedRescheduledTaskData['priority']=parseInt(newRescheduledData['priority'])
    fetch(`/reschedule-task/${newRescheduledData['id']}`,{
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(parsedRescheduledTaskData)
    }).then(async (data)=>{
        msg = await data.json()
        alert(msg['message'])
    }).catch((err)=>{
        alert("Error happened: "+err)
    })
    .finally(()=>location.reload(true))
})

priority.addEventListener("input",()=>{
    priorityInput.value=priority.value
})

addTaskBtn.addEventListener("click",()=>{
    newTaskDialog.showModal()
})

closeAddFormBtn.addEventListener("click",()=>{
    newTaskDialog.close()
})

closeRescheduleFormBtn.addEventListener("click",()=>{
    rescheduleTaskDialog.close()
})

tasksContainer.addEventListener("click",async (e)=>{
    const task = e.target.closest(".task")
    const closeBtn = e.target.closest('.close-btn')
    const completedBtn = e.target.closest('.completed-btn')
    const rescheduleBtn = e.target.closest('.reschedule-btn')
    const cancelBtn = e.target.closest('.cancel-btn')
    if(task !== null && !task.classList.contains("expanded")){
        let rawData = await fetch(`/get-expanded-task/${task.dataset.taskId}`)
        task.innerHTML = await rawData.text()
        task.classList.add("expanded")
    }
    if(closeBtn !== null){
        let rawData = await fetch(`/get-task/${task.dataset.taskId}`)
        task.outerHTML = await rawData.text()
        task.classList.remove("expanded")
    }
    if(completedBtn !== null){
        await fetch(`/mark-completed/${task.dataset.taskId}`)
        location.reload(true)
    }
    if(rescheduleBtn !== null){
        const taskData =  await fetch(`/get-task-data/${task.dataset.taskId}`)
        const parsedTaskData = await taskData.json()
        rescheduleId.value = parsedTaskData['id']
        rescheduleName.value = parsedTaskData['name']
        rescheduleDescription.value = parsedTaskData['description']
        rescheduleDate.value = parseDate(parsedTaskData['starting_date'])
        let resTime =  parsedTaskData['starting_time'].split(":")
        rescheduleHour.value = getHour(parseInt(resTime[0]))
        rescheduleMin.value = resTime[1]
        rescheduleTimePeriod.value = (parseInt(resTime[0]) >= 12 ? 'pm':'am')
        rescheduleDuration.value =  parsedTaskData['duration']
        rescheduleDurationUnit.value = parsedTaskData['duration_unit']
        reschedulePriority.value = parsedTaskData['priority']
        rescheduleTaskDialog.showModal();

    }

    if(cancelBtn !== null){
        await fetch(`/mark-cancelled/${task.dataset.taskId}`)
        location.reload(true)
    }
})

