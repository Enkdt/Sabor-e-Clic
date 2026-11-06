import { useNavigate } from 'react-router-dom'
import { useAuth } from '../authContext'
import { useTheme } from '../themeContext'
import { Header } from '../Components/Header'
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
