import { Banner } from '../Assets/Banner'
import { CardBancada } from './CardBancada'
import './AgdBancada.css'
import { useEffect, useState } from 'react'
export const AgdBancada=()=>{
    const [bancadas, setBancadas] = useState([])
    const [status, setStatus] = useState('loading')
    useEffect(() => {
        let active = true
        fetch('/api/bancadas', { credentials: 'include' })
            .then(async (response) => {
                const data = await response.json()
                if (!response.ok) throw new Error(data.error?.message || 'Não foi possível carregar as bancadas.')
                return data.bancadas || []
            })
            .then((items) => { if (active) { setBancadas(items); setStatus('ready') } })
            .catch(() => { if (active) setStatus('error') })
        return () => { active = false }
    }, [])
    return (
        <>
            <Banner/>
            <div>
                <h1>Agende uma Bancada</h1>
            </div>
            <div>
                Agende com a Sabor&Click uma bancada com todos os itens necessários para tornar suas receitas ainda mais deliciosas
            </div>

            <div>
                <h1>Horários e datas disponíveis</h1>
            </div>

            {status === 'loading' && <p>Carregando bancadas…</p>}
            {status === 'error' && <p role="alert">Não foi possível carregar as bancadas.</p>}
            {status === 'ready' && bancadas.length === 0 && <p>Nenhuma bancada disponível no momento.</p>}
            {bancadas.map((bancada) => <CardBancada key={bancada.id} bancada={bancada} />)}
        </>
    )
}
