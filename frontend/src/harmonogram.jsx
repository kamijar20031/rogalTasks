import {useState, useEffect} from "react"




const Harmonogram = ({backendLink, harmonogram, zamknijOkno, blad, callback, userID}) => {

    const [nazwa, setName] = useState("");
    const [currentH, setCurrent] = useState("new");
    const [currentHID, setCurrentID] = useState("new");
    const [reset, resetThisSH] = useState(false);
    const [intervalMode, setIntervalMode] = useState(0);
    const [intervalVal,setIntervalVal] = useState(1);
    const intervalModeMap = [{nazwa:"Dni", type:"daily", val:"0"},{nazwa:"Tygodnie", type:"weekly", val:"1"}];
    const [dayTime, setDayTime] = useState("12:00");
    const currentTime = new Date();
    currentTime.setDate(currentTime.getDate()+1);
    const [data, setDate] = useState(`${currentTime.getFullYear()}-${`${currentTime.getMonth()+1}`.padStart(2, 0)}-${`${currentTime.getDate()}`.padStart(2, 0)}`);
    
    class dzien {
        static counter = 0;
        constructor({ nazwa, hour="12:00", check=false, id} = {}) {
            this.id = id ?? dzien.counter++;
            this.nazwa = nazwa;
            this.hour = hour;
            this.check = check;
        }
        copy(changes = {}) {
            return new dzien({
                id: this.id,
                nazwa: this.nazwa,
                hour: this.hour,
                check: this.check,
                ...changes
            })
        }
    }
    
    const [dniTygodnia, setDniTygodnia] = useState([new dzien({nazwa:"Poniedziałek"}), new dzien({nazwa:"Wtorek"}), new dzien({nazwa:"Środa"}), new dzien({nazwa:"Czwartek"}), new dzien({nazwa:"Piątek"}), new dzien({nazwa:"Sobota"}), new dzien({nazwa:"Niedziela"})]);

    harmonogram["new"] = {nazwa: "Nazwa",dni:[]};
    const updateDni = (id, changes) => {
        setDniTygodnia(prev =>
            prev.map(dni =>
                dni.id === id ? dni.copy(changes) : dni));
    }


    const removeH = async (ID) =>
    {
        const url = `${backendLink}harmoRemove/${ID}`;
        const options = {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json"
            },
        }
        const response = await fetch(url, options);
        setH("new")
        resetThisSH(!reset)
        zamknijOkno();
        callback();

    }
    const parseToDay = (dni) => {
        console.log(dni)
        setDate(dni.date)
        setDayTime(dni.time)
        setIntervalVal(dni.interval)
        setIntervalMode(0)
    }
    const parseToWeek = (dni) => {
        console.log(dni)
        setIntervalVal(dni.interval)
        setIntervalMode(1)
        dni.days.forEach(day => {
            updateDni(day.id, {hour: `${String(day.hour).padStart(2, '0')}:${String(day.minute).padStart(2, '0')}`, check: true})
        })

    }
    const resetDays = () => {
        setIntervalVal(1)
        setIntervalMode(0)
        dniTygodnia.forEach(day => {
            updateDni(day.id, {hour: "12:00", check: false})
        })
        setDate(`${currentTime.getFullYear()}-${`${currentTime.getMonth()+1}`.padStart(2, 0)}-${`${currentTime.getDate()}`.padStart(2, 0)}`)
        setDayTime("12:00")
    }
    const setH = (e) =>
    {
        if (e!="new")
        {
            setName("");
            e = parseInt(e)
            setCurrentID(e)
            var elementPos = harmonogram.map((x) => {return x.ID; });
            var id = elementPos.indexOf(e)
            setCurrent(id)
            if (harmonogram[id].dni.type=="daily")
                parseToDay(harmonogram[id].dni)
            else
                parseToWeek(harmonogram[id].dni)
        }
        else
        {
            resetDays()
            setName("");
            setCurrentID(e)
            setCurrent(e)
        }

    }

    const parseDniDay = () => {
        return {type:"daily", interval:intervalVal, time: dayTime, date: data}
    }
    const parseDniWeek = () => {
        var temp = []
        dniTygodnia.forEach((dzien)=>
        {
            if (dzien.check)
            {
                var [hour, minute] = dzien.hour.split(':').map(Number);
                temp.push({id:dzien.id, hour:hour, minute:minute})
            }
        })
        return {type:"weekly", interval:intervalVal, days: temp}
    }

    const onSubmit = async(e) => {
        e.preventDefault()
        var dniD;
        if (intervalMode==0)
            dniD = parseDniDay()
        else
            dniD = parseDniWeek()
        
        var dane = {
            nazwa, dniD
        }
        var status = 0;
        
        if (currentHID=="new")
        {
            const url = `${backendLink}harmonogramCreate/${userID}`
            const options = {
                method: "POST",
                headers:  {
                    "Content-Type" : "application/json"
                },
                body: JSON.stringify(dane)
            }
            const response = await fetch(url, options);
            status = response.status

        }
        else
        {
            if (nazwa=="")
                dane.nazwa = harmonogram[currentH].nazwa
            const url = `${backendLink}harmonogramEdit/${currentHID}`
            const options = {
                method: "PATCH",
                headers:  {
                    "Content-Type" : "application/json"
                },
                body: JSON.stringify(dane)
            }
            const response = await fetch(url, options);
            status = response.status
        }
        if (status != 400 && status!=401)
        {
            setH("new")
            zamknijOkno();
            resetThisSH(!reset)
            callback();
        }
        else
            blad(1);
    }

    useEffect(()=>{

    },[reset])

    return <form onSubmit={onSubmit}>
            <div style={{fontSize:"2vw", fontWeight:"bold", marginBottom:"1.1vw"}}>Harmonogram</div>
             <select id='aktywnosc' onChange={(e) => setH(e.target.value)} value={currentHID} selected="new">
                 <option value='new'>Dodaj nowa aktywnosc</option>
               {harmonogram.map((h) => (
                <option key={h["ID"]} value={h['ID']}>{h['nazwa']}</option>
                 ))}
             </select>

            <span id="error-message-form"></span>
             <input id='nazwa' type='text' value={nazwa} onChange={(e) => setName(e.target.value)} placeholder={harmonogram[currentH].nazwa}></input>
            <h2>Odstęp czasu</h2>
            <select id='intervalMode' onChange={(e) => setIntervalMode(parseInt(e.target.value))} value={intervalMode} selected='0'>
               {intervalModeMap.map((inter) => (
                <option key={inter["val"]} value={inter["val"]}>{inter['nazwa']}</option>
                 ))}
             </select>
             <input id='intervalVal' type='number' value={intervalVal} onChange={(e) => setIntervalVal(e.target.value)} min='1'></input>
            {intervalMode==0&&
                <>
                    <h2>Godzina</h2>
                    <input type='time' id='timeDay' value={dayTime} onChange={(e) =>setDayTime(e.target.value)}></input>
                    <h2>Start</h2>
                    <input type="date" id="dayData" value={data} onChange={(e) => setDate(String(e.target.value))}/>
                </>
            }
            {intervalMode==1&&
                <div className="overflow-auto max-h-[20vh]">
                    <h2>Dni tygodnia</h2>
                    
                    {dniTygodnia.map((dzien) =>(
                        <>
                        <div className="w-fit m-6 flex mx-auto items-center" key={dzien.id}>
                        
                            <label className="flex items-center gap-5 cursor-pointer" >{dzien.nazwa}
                            <input type='checkbox' checked={dzien.check} onChange={(e) => {updateDni(dzien.id, {check: !dzien.check})}}></input></label>
                            
                        </div>
                        {dzien.check&&<input type='time' value={dzien.hour} onChange={(e) =>updateDni(dzien.id, {hour: e.target.value})}></input>}
                        </>
                    ))}
                    
                </div>
            }
            {currentH!="new"&&<><button onClick={(e) => {e.preventDefault(); removeH(harmonogram[currentH].ID)}}>Usuń wybraną aktywność</button><button type='submit' >Edytuj</button></>}
            {currentH=="new"&&<button type='submit' >Dodaj</button>}
    </form>
}

export default Harmonogram