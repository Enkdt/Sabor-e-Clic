import { useEffect, useState } from 'react'
import { Header } from '../Components/Header'
import { CardBancada } from './CardBancada'
import './AgdBancada.css'

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
        <main className='agdBancadaPage'>
            <Header/>
            <div className='agdBancadaContent'>
                <p className='agdBancadaEyebrow'>Para donos de restaurante e microempreendedores</p>
                <h1 className='agdBancadaTitle'>Agende uma bancada</h1>
                <p className='agdBancadaSubtitle'>
                    Agende com a Sabor&amp;Click uma bancada com todos os itens necessários para tornar suas receitas ainda mais deliciosas.
                </p>

                <h2 className='agdBancadaSectionTitle'>Horários e datas disponíveis</h2>

                {status === 'loading' && <p role='status'>Carregando bancadas…</p>}
                {status === 'error' && <p role='alert'>Não foi possível carregar as bancadas.</p>}
                {status === 'ready' && bancadas.length === 0 && <p>Nenhuma bancada disponível no momento.</p>}

                <div className='agdBancadaList'>
                    {status === 'ready' && bancadas.map((bancada) => <CardBancada key={bancada.id} bancada={bancada} />)}
                </div>
            </div>
        </main>
    )
}
