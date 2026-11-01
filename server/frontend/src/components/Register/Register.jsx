import React, {useState} from 'react';
import {Link} from 'react-router-dom';
import {api} from '../../App';

export default function AuthForm({register, onSuccess}) {
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(event) {
    event.preventDefault(); setError(''); setBusy(true);
    const values = Object.fromEntries(new FormData(event.currentTarget));
    if (register && values.password !== values.confirmPassword) {
      setError('Passwords must match.'); setBusy(false); return;
    }
    delete values.confirmPassword;
    try {
      const user = await api(register ? 'register' : 'login', values);
      onSuccess(user);
      sessionStorage.setItem('username', user.userName);
      window.location.assign('/');
    } catch (err) {setError(err.message);} finally {setBusy(false);}
  }
  return <section className="auth-card">
    <p className="eyebrow">BESTCARS · YOUR NEXT CHAPTER</p>
    <h1>{register ? 'Create your account' : 'Welcome back'}</h1>
    <p>{register ? 'Join the community and share your dealership experience.' : 'Sign in to write reviews and manage your account.'}</p>
    <form onSubmit={submit}>
      {register && <div className="name-fields"><label>First name<input name="firstName" autoComplete="given-name" required maxLength="150" /></label><label>Last name<input name="lastName" autoComplete="family-name" required maxLength="150" /></label></div>}
      <label>Username<input name="userName" autoComplete="username" required maxLength="150" /></label>
      {register && <label>Email<input name="email" type="email" autoComplete="email" required /></label>}
      <label>Password<input name="password" type="password" autoComplete={register ? 'new-password' : 'current-password'} required /></label>
      {register && <><label>Confirm password<input name="confirmPassword" type="password" autoComplete="new-password" required /></label><small>Use at least 8 characters and avoid common passwords or personal information.</small></>}
      {error && <p className="error" role="alert">{error}</p>}
      <button disabled={busy} type="submit">{busy ? 'Please wait…' : register ? 'Create account' : 'Sign in'}</button>
    </form>
    <p>{register ? 'Already have an account? ' : 'New to BestCars? '}<Link to={register ? '/login' : '/register'}>{register ? 'Sign in' : 'Register'}</Link></p>
  </section>;
}

