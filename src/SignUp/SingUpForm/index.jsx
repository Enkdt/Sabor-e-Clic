import { useState } from 'react'
import { AddressSelect } from '../../Components/AddressSelect'
import { Input } from '../../Components/Input'
import { NextBtn } from '../../Components/NextBtn'
import './SignUpForm.css'
export const SignUpForm=()=>{

    const [nome,setNome]=useState('');
    const [sobrenome,setSobrenome]=useState('');
    const [email,setEmail]=useState('');
    const [rua,setRua]=useState('');
    const [num,setNum]=useState('');
    const [comp,setComp]=useState('');
    const [senha,setSenha]=useState('');
    const [confSenha,setConfSenha]=useState('');

    const inputs=[
        {
            label:"Nome",
            placeholder:"Primeiro nome",
            type:"text",
            value: nome,
            onChange: (e) => setNome(e.target.value)
        },
        {
            label:"Sobrenome",
            placeholder:"Insira seu sobrenome",
            type:"text",
            value: sobrenome,
            onChange: (e) => setSobrenome(e.target.value)
        },
        {
            label:"Email",
            placeholder:"exemplo@email.com",
            type:"text",
            value: email,
            onChange: (e) => setEmail(e.target.value)
        }
    ]

    const sendSignUp=(e)=>{
        e.preventDefault();
        console.log(`Formulário Enviado - Dados
            =======================
            ${nome}
            ${sobrenome}`)
    }

    return(
        <div className='signupForm'>
            <h1 className='transition-all duration-500 ease text-[44px] md:text-[54px] lg:text-[64px]'>Bem-vindo!</h1>
            <h3 className='transition-all duration-500 ease text-[14px] lg:text-[16px]'>Cadastre-se para aproveitar todo nosso app</h3>
            <form onSubmit={sendSignUp}>
            {inputs.map((input) => (
                                <div key={input.label}>
                                    <Input
                                        label={input.label}
                                        placeholder={input.placeholder}
                                        type={input.type}
                                        onChange={input.onChange}
                                        value={input.value}
                                        className="loginInput"
                                    />
                                </div>
                            ))}
            <label className='addressLabel'>Endereço</label>
            <AddressSelect/>
            <Input label="Rua" placeholder="Ex: Rua Augusta" type="text" className="loginInput" onChange={(e) => setRua(e.target.value)}/>
            <div className='divNumComp'>
                <Input label="Número" placeholder="Ex: 120" type="text" className="loginInput" onChange={(e) => setNum(e.target.value)}/>
                <Input label="Complemento" placeholder="Ex: apto 13" type="text" className="loginInput" onChange={(e) => setComp(e.target.value)}/>
            </div>
                <Input label="Senha" placeholder="Crie sua senha" type="password" className="loginInput" onChange={(e) => setSenha(e.target.value)}/>
                <Input label="Confirmação Senha" placeholder="Repita a senha criada" type="password" className="loginInput" onChange={(e) => setConfSenha(e.target.value)}/>
                <NextBtn text="Criar Conta"/>
            </form>
        </div>
    )
}