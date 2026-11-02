import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAuth } from '../authContext'
import { Banner } from '../Assets/Banner'
import { BancadaImg } from '../Assets/BancadaImg'
import { getCsrfToken } from '../authSession'
import './Bancada.css'

const brl = (value) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)

export const Bancada = () => {
    const { id } = useParams()
    const { user } = useAuth()
    const [bancada, setBancada] = useState(null)
    const [status, setStatus] = useState('loading')
    const [inicio, setInicio] = useState('')
    const [fim, setFim] = useState('')
    const [message, setMessage] = useState('')
    const [busy, setBusy] = useState(false)

    useEffect(() => {
        let active = true
        fetch(`/api/bancadas/${encodeURIComponent(id)}`, { credentials: 'include' })
            .then(async (response) => {
                const data = await response.json()
                if (!response.ok) throw new Error(data.error?.message || 'Bancada não encontrada.')
                return data.bancada
            })
            .then((item) => { if (active) { setBancada(item); setStatus('ready') } })
            .catch(() => { if (active) setStatus('error') })
        return () => { active = false }
    }, [id])

    const estimativa = useMemo(() => {
        if (!inicio || !fim || !bancada) return null
        const minutos = (new Date(fim).getTime() - new Date(inicio).getTime()) / 60000
        if (!Number.isFinite(minutos) || minutos <= 0) return null
        return { minutos, preco: Number(bancada.preco_hora) * minutos / 60 }
    }, [inicio, fim, bancada])

    async function submit(event) {
        event.preventDefault()
        if (!bancada || !estimativa) return
        const formElement = event.currentTarget
        setBusy(true)
        setMessage('')
        try {
            const csrfToken = await getCsrfToken()
            const response = await fetch(`/api/bancadas/${encodeURIComponent(id)}/agendamentos`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ inicio, fim }),
            })
            const data = await response.json()
            if (!response.ok) throw new Error(data.error?.message || 'Não foi possível criar o agendamento.')
            setMessage(`Agendamento confirmado. Duração: ${data.agendamento.tempo_agendado} min. Total: ${brl(Number(data.agendamento.preco_total))}.`)
            setInicio('')
            setFim('')
            formElement.reset()
        } catch (error) {
            setMessage(error.message || 'Não foi possível conectar ao servidor.')
        } finally {
            setBusy(false)
        }
    }

    return <>
        <Banner />
        {status === 'loading' && <p>Carregando bancada…</p>}
        {status === 'error' && <p role="alert">Não foi possível encontrar esta bancada.</p>}
        {status === 'ready' && bancada && <div>
            <BancadaImg />
            <div>
                <h1>{bancada.nome}</h1>
                {bancada.endereco
                    ? <p>{bancada.endereco.rua}, {bancada.endereco.numero}{bancada.endereco.complemento ? ` — ${bancada.endereco.complemento}` : ''}<br />{bancada.endereco.bairro} — {bancada.endereco.cidade}, {bancada.endereco.estado}</p>
                    : <p>Endereço não cadastrado.</p>}
                <p>Valor por hora: <strong>{brl(Number(bancada.preco_hora))}</strong></p>
                <p>Conheça os recursos disponíveis para preparar suas receitas.</p>
                <p>Equipamentos:</p>
                <ol>
                    {bancada.equipamentos.length
                        ? bancada.equipamentos.map((item, index) => <li key={`${item.nome}-${index}`}>{item.quantidade > 1 ? `${item.quantidade} × ` : ''}{item.nome}</li>)
                        : <li>Nenhum equipamento cadastrado.</li>}
                </ol>
            </div>
            <div>
                <br />
                {user?.role === 'cook' ? <>
                    <p>Horários disponíveis: {bancada.horarios_disponiveis.length
                        ? bancada.horarios_disponiveis.map((faixa) => `${faixa.inicio}–${faixa.fim}`).join(', ')
                        : 'sem horários cadastrados'}</p>
                    <form onSubmit={submit}>
                        <label>Início
                            <input name="inicio" type="datetime-local" required value={inicio} onChange={(event) => setInicio(event.target.value)} />
                        </label>
                        <label>Fim
                            <input name="fim" type="datetime-local" required value={fim} onChange={(event) => setFim(event.target.value)} />
                        </label>
                        {estimativa && <p>Duração: {estimativa.minutos} minutos · Total estimado: {brl(estimativa.preco)}</p>}
                        <button type="submit" disabled={busy || !estimativa}>{busy ? 'Agendando…' : 'Confirmar'}</button>
                    </form>
                </> : <p>O agendamento de bancadas está disponível para cozinheiros.</p>}
                <p role="status">{message}</p>
                <Link to="/catalogo/bancadas">Voltar ao catálogo</Link>
            </div>
        </div>}
    </>
}
