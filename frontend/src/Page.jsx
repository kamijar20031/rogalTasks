import { useState, useEffect } from 'react'
import ZadaniaLista from "./zadania.jsx"
import ZadForm from "./noweZadania.jsx"
import Harmonogram from "./harmonogram.jsx"
import UserConfig from "./user.jsx"
import './App.css'
import './css/fontello.css'


function Page({backendLink, user, setCookie}) {
  const [zadania, pobierz] = useState([]);
  const [userData, userSet] = useState([]);
  const [harmonogram, harmoSet] = useState("")
  const [trybGlobal, trybSet] = useState([0]);
  const [oknoTaskForm, oknoTaskFormEnable] = useState(false);
  const [specificDate, setSpecificDate] = useState("any")


  const pobierzUser = async () => {
    const response = await fetch(`${backendLink}userData/${user}`);
    const data = await response.json();
    userSet(data.dane);

  }

  const pobierzZadania = async (date) =>   {
    const response = await fetch(`${backendLink}zadania/${user}/${date}`);
    const data = await response.json();
    pobierz(data.zadania);
  }

    const pobierzHarmonogram = async () =>   {
        const response = await fetch(`${backendLink}harmonogram/${user}`);
        const data = await response.json();
        var newData = data.harmonogram;
        harmoSet(newData);
    }


  const bladOkna = (type) => {
    if (type==0 || type==1)
    {
        document.getElementById("error-message-form").innerHTML = "Musisz dodać wszystkie wartości do formularza!";
    }
    document.getElementsByClassName("modal-content")[0].classList.add("modal-content-error");
    document.getElementsByClassName("modal-content")[0].classList.remove("modal-content");
    setTimeout(() => {
      document.getElementsByClassName("modal-content-error")[0].classList.add("modal-content");
      document.getElementsByClassName("modal-content")[0].classList.remove("modal-content-error");
    }, 2000)
  }

  const zamknijOkno = (tryb) =>{
      if (oknoTaskForm) 
      { 
        trybSet(tryb)
        oknoTaskFormEnable(false);
        document.getElementsByClassName("modal")[0].classList.add("modal-hidden");
        document.getElementsByClassName("modal")[0].classList.remove("modal");
        if (tryb!=2)
          document.getElementById("error-message-form").innerHTML = "";
      }
    
  }

  const otworzOkno = (tryb) => {
    if (!oknoTaskForm ) 
    {
        trybSet(tryb)
        oknoTaskFormEnable(true);
        document.getElementsByClassName("modal-hidden")[0].classList.add("modal");
        document.getElementsByClassName("modal-hidden")[0].classList.remove("modal-hidden");
    }


  }

  const logout = () => {
    setCookie("loginID", "")
  }

  const update = (date=specificDate) => {
      setSpecificDate(date)
      pobierzZadania(date);
      pobierzHarmonogram();
      pobierzUser();
  }

  useEffect(() => {
    update();
    const interval = setInterval(() => {
      update()(t => t + 1); 
    }, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [])

  return <>
  
    <div id='buttonsLayout'>
      <button onClick={ () => {otworzOkno(0)}}><i className="icon-plus"></i></button>
      <button className='optional' onClick={ () => {otworzOkno(1)}}><i className="icon-calendar-plus-o"></i></button>
      <button className='optional' onClick={ () => {otworzOkno(3)}}><i className="icon-address-book-o"></i></button>
      <button  onClick={ () => {logout()}}><i className="icon-logout"></i></button>
    </div>
    
    <div className="modal-hidden">
      <div className="modal-content">
        <span className="close" onClick = {zamknijOkno}>&times;</span>
        {trybGlobal==0 &&<ZadForm backendLink={backendLink} zadania={zadania} zamknijOkno = {() => {zamknijOkno(0)}} blad={bladOkna} callback={update} userID={user}/>}
        {trybGlobal==1 &&<Harmonogram backendLink={backendLink} harmonogram={harmonogram} zamknijOkno = {() => {zamknijOkno(1)}} blad={bladOkna} callback={update} userID={user}/>}
        {trybGlobal==3 &&<UserConfig backendLink={backendLink} dane={userData} zamknijOkno = {() => {zamknijOkno(3)}} blad={bladOkna} userID={user} callback={update} logout={logout}/>}
      </div>

    </div>
    {specificDate!="any" &&<div><div style={{margin:"auto", textAlign:'center', marginTop: "5vh", fontSize: "3vh"}}>Zadania dla {specificDate}</div><button onClick={() => {update("any")}} style={{marginTop:"1vh"}}>Resetuj</button></div>}
    <ZadaniaLista backendLink={backendLink} zadania={zadania} callback={update} />
  </>
}

export default Page
