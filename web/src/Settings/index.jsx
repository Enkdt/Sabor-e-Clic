import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../authContext'
import { useTheme } from '../themeContext'
import { Header } from '../Components/Header'
import { ImageUploader } from '../Components/ImageUploader'
import { fetchAvatar, setAvatar } from '../authSession'
import './Settings.css'

const THEME_OPTIONS=[
    { value:'light', label:'Claro' },
    { value:'dark', label:'Escuro' },
    { value:'system', label:'Seguir o sistema' },
]

export const Settings=()=>{
    const { preference, setPreference, effective }=useTheme()
    const { user, logout }=useAuth()
    const navigate=useNavigate()
    const [avatar,setAvatarUrl]=useState(null)
    const [fotoMsg,setFotoMsg]=useState(null) // feedback da troca de foto

    useEffect(()=>{
        if(!user) return
        let active=true
        fetchAvatar()
            .then((url)=>{ if(active) setAvatarUrl(url) })
            .catch(()=>{}) // avatar ausente não deve quebrar as configurações
        return ()=>{ active=false }
    },[user])

    const trocarFoto=async (key,url)=>{
        setAvatarUrl(url)
        setFotoMsg(null)
        try{ await setAvatar(key); setFotoMsg({ tipo:'ok', texto:'Foto atualizada.' }) }
        catch(err){ setFotoMsg({ tipo:'erro', texto:err.message || 'Não foi possível salvar a foto.' }) }
    }

    const handleLogout=async ()=>{
        try{ await logout() }finally{ navigate('/') }
    }

    return(
        <main className='settingsPage'>
            <Header/>
            <div className='settingsContent'>
                <h1>Configurações</h1>

                <section className='settingsSection' aria-labelledby='settings-theme-title'>
                    <h2 id='settings-theme-title'>Aparência</h2>
                    <fieldset className='settingsFieldset'>
                        <legend>Tema</legend>
                        {THEME_OPTIONS.map((option)=>(
                            <label key={option.value} className='settingsRadio'>
                                <input
                                    type='radio'
                                    name='theme'
                                    value={option.value}
                                    checked={preference===option.value}
                                    onChange={()=>setPreference(option.value)}
                                />
                                <span>{option.label}</span>
                            </label>
                        ))}
                    </fieldset>
                    <p className='settingsHint' role='status'>
                        Tema atual: {effective==='dark' ? 'escuro' : 'claro'}
                        {preference==='system' ? ' (seguindo o sistema)' : ''}.
                    </p>
                </section>

                {user && (
                    <section className='settingsSection' aria-labelledby='settings-photo-title'>
                        <h2 id='settings-photo-title'>Foto</h2>
                        <ImageUploader current={avatar} label='foto' shape='round' onUpload={trocarFoto}/>
                        {fotoMsg && (
                            <p className={fotoMsg.tipo==='ok' ? 'settingsPhotoOk' : 'settingsPhotoErro'} role={fotoMsg.tipo==='ok' ? 'status' : 'alert'}>
                                {fotoMsg.texto}
                            </p>
                        )}
                    </section>
                )}

                {user && (
                    <section className='settingsSection' aria-labelledby='settings-account-title'>
                        <h2 id='settings-account-title'>Conta</h2>
                        <p>{user.email}</p>
                        <button type='button' className='settingsLogout' onClick={handleLogout}>Sair da conta</button>
                    </section>
                )}
            </div>
        </main>
    )
}
