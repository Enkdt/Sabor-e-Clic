import { useState } from 'react'
import { AddressSelect } from '../../Components/AddressSelect'
import { Input } from '../../Components/Input'
import { NextBtn } from '../../Components/NextBtn'
import './SignUpForm.css'
import { NavLink, useNavigate } from 'react-router-dom';
import { CheckCircleIcon, CheckFatIcon, CheckIcon } from '@phosphor-icons/react'
export const SignUpForm=()=>{

    const navigate=useNavigate();

    const [nome,setNome]=useState('');
    const [sobrenome,setSobrenome]=useState('');
    const [email,setEmail]=useState('');
    const [rua,setRua]=useState('');
    const [num,setNum]=useState('');
    const [comp,setComp]=useState('');
    const [senha,setSenha]=useState('');
    const [confSenha,setConfSenha]=useState('');
    const [endereco, setEndereco] = useState({
    country: null,
    state: null,
    city: null
    });

    const tem8Caracteres = senha.length >= 8;
    const temMaiuscula = /[A-Z]/.test(senha);
    const temMinuscula = /[a-z]/.test(senha);
    const temEspecial = /[^A-Za-z0-9]/.test(senha);

    const senhasCoincidem= senha === confSenha;

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

    const [error, setError] = useState('');
  
    const sendSignUp = async (e) => {
        e.preventDefault();

        try {
            const response = await fetch('/api/cadastro', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: nome,
                    surname: sobrenome,
                    email: email,
                    password: senha,
                    password_confirmation: confSenha,
                    cep:null,
                    country: endereco.country.name,
                    state: endereco.state.name,
                    city: endereco.city.name,
                    street: rua,
                    number: num,
                    extra: comp,
                })
            });

            const data = await response.json();

            console.log(data);

            if (!response.ok) {
                setError(data.error.message);
                return;
            }

            navigate('/');

        } catch(error){
            //teste
            setError('Não foi possível conectar ao servidor.');
        }
    };

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
            <AddressSelect onAddressChange={setEndereco}/>
            <Input label="Rua" placeholder="Ex: Rua Augusta" type="text" className="loginInput" onChange={(e) => setRua(e.target.value)}/>
            <div className='divNumComp'>
                <Input label="Número" placeholder="Ex: 120" type="text" className="loginInput" onChange={(e) => setNum(e.target.value)}/>
                <Input label="Complemento" placeholder="Ex: apto 13" type="text" className="loginInput" onChange={(e) => setComp(e.target.value)}/>
            </div>
                <Input label="Senha" placeholder="Crie sua senha" type="password" className="loginInput" onChange={(e) => setSenha(e.target.value)}/>
                <p className='ReqP'>Sua senha deve conter ao mínimo:</p>
                <ul className='pwdReq'>
                    <div className={senha.length===0 ? '' : tem8Caracteres ? 'valido' : 'invalido'}>
                        <CheckCircleIcon weight='fill' className='checkIcon'/><li>8 caracteres</li>
                    </div>
                    <div className={senha.length===0 ? '' : temMaiuscula && temMinuscula ? 'valido' : 'invalido'}>
                        <CheckCircleIcon weight='fill' className='checkIcon'/><li>1 letra maíuscula e minúscula</li>
                    </div>
                    <div className={senha.length===0 ? '' : temEspecial ? 'valido' : 'invalido'}>
                        <CheckCircleIcon weight='fill' className='checkIcon'/><li>1 caractere especial</li>
                    </div>
                </ul>
                <Input label="Confirmação Senha" placeholder="Repita a senha criada" type="password" className="loginInput" onChange={(e) => setConfSenha(e.target.value)}/>
                <span className={confSenha.length===0? 'confNeutro' : senhasCoincidem ? 'confNeutro' : 'confInvalido'}>As senhas não coincidem!</span>
                <NextBtn text="Criar Conta"/>
            </form>
                {error && (
    <p className="signupError">
        {error}
    </p>
    )}
        </div>
    )
}