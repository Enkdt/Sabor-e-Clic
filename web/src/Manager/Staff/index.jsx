import { useState } from 'react'
import { createStaff } from '../../authSession'
import { Header } from '../../Components/Header'
import { Input } from '../../Components/Input'
import { NextBtn } from '../../Components/NextBtn'
import './Staff.css'

export const Staff=()=>{
    const [role,setRole]=useState('cook')
    const [nome,setNome]=useState('')
    const [email,setEmail]=useState('')
    const [password,setPassword]=useState('')
    const [especialidade,setEspecialidade]=useState('')
    const [nivel,setNivel]=useState('1')
    const [status,setStatus]=useState('idle') // idle | saving | done | error
    const [errors,setErrors]=useState({})
    const [message,setMessage]=useState('')

    const submit=async (e)=>{
        e.preventDefault()
        if(status==='saving') return
        setStatus('saving'); setErrors({}); setMessage('')
        const payload={ role, nome, email, password }
        if(role==='cook') payload.especialidade=especialidade
        else payload.nivel_permissao=Number(nivel)
        try{
            const user=await createStaff(payload)
            setStatus('done')
            setMessage(`Conta criada: ${user.nome} (${user.role}). Para filiar um cozinheiro a restaurantes, use a página Filiações.`)
            setNome(''); setEmail(''); setPassword(''); setEspecialidade(''); setNivel('1')
        }catch(error){
            setStatus('error')
            setErrors(error.fields || {})
            setMessage(error.fields ? 'Corrija os campos destacados.' : error.message)
        }
    }

    return(
        <main className='staffPage'>
            <Header/>
            <div className='staffForm px-4 py-8 md:px-10 lg:px-[88px]'>
                <h1 className='text-[28px] md:text-[36px]'>Criar conta de equipe</h1>
                <form onSubmit={submit}>
                    <div className='staffField'>
                        <label htmlFor='staff-role'>Tipo de conta</label>
                        <select id='staff-role' value={role} onChange={(e)=>setRole(e.target.value)}>
                            <option value='cook'>Cozinheiro</option>
                            <option value='admin'>Administrador</option>
                        </select>
                    </div>

                    <Input label='Nome' placeholder='Nome completo' type='text' value={nome} onChange={(e)=>setNome(e.target.value)} className='loginInput'/>
                    {errors.nome && <p role='alert' className='staffError'>{errors.nome}</p>}

                    <Input label='Email' placeholder='email@exemplo.com' type='email' value={email} onChange={(e)=>setEmail(e.target.value)} className='loginInput'/>
                    {errors.email && <p role='alert' className='staffError'>{errors.email}</p>}

                    <Input label='Senha' placeholder='Senha forte' type='password' value={password} onChange={(e)=>setPassword(e.target.value)} className='loginInput'/>
                    {errors.password && <p role='alert' className='staffError'>{errors.password}</p>}

                    {role==='cook' ? (
                        <>
                            <Input label='Especialidade' placeholder='Ex.: Vegana' type='text' value={especialidade} onChange={(e)=>setEspecialidade(e.target.value)} className='loginInput'/>
                            {errors.especialidade && <p role='alert' className='staffError'>{errors.especialidade}</p>}
                        </>
                    ) : (
                        <div className='staffField'>
                            <label htmlFor='staff-nivel'>Nível de permissão (1–5)</label>
                            <select id='staff-nivel' value={nivel} onChange={(e)=>setNivel(e.target.value)}>
                                {[1,2,3,4,5].map((n)=>(<option key={n} value={String(n)}>{n}</option>))}
                            </select>
                            {errors.nivel_permissao && <p role='alert' className='staffError'>{errors.nivel_permissao}</p>}
                        </div>
                    )}

                    {message && <p role={status==='error' ? 'alert' : 'status'} className={status==='error' ? 'staffError' : 'staffSuccess'}>{message}</p>}
                    <NextBtn text={status==='saving' ? 'Criando…' : 'Criar conta'}/>
                </form>
            </div>
        </main>
    )
}
