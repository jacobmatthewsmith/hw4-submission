import { Link } from 'react-router-dom'

export default function About() {
  return (
    <section className="section about">
      <div className="page-head">
        <p className="eyebrow">About Us</p>
        <h1>A small shop with an unreasonable amount of navy.</h1>
      </div>

      <div className="about-body">
        <p>
          Campus Customs started with a simple observation: everyone in New Haven owns at least one
          Bulldog sweatshirt, and nobody can remember where they got it. We decided to be the answer
          to that question.
        </p>
        <p>
          From our spot on Broadway, a short walk from just about every lecture hall worth skipping (we
          kid, go to class), we stock the layers that get you through a New England year: heavyweight
          hoodies for January, crewnecks for the first crisp day in October, and tees for the three
          warm weeks in between.
        </p>

        <h2>What we're about</h2>
        <ul className="about-list">
          <li>
            <strong>School spirit, no homework required.</strong> Whether you're a first-year, a
            fifth-year, a proud parent, or a grandparent who just learned what a “residential college”
            is, there's something here with your name on it. Sometimes literally.
          </li>
          <li>
            <strong>Every corner of campus.</strong> Residential colleges, varsity sports, club teams,
            and the graduate schools all get their own gear, because loyalty comes in more than one
            crest.
          </li>
          <li>
            <strong>Honest answers.</strong> Ask us (or our chat assistant) about price, sizing, or
            stock, and you'll get the real number, even when that number is zero.
          </li>
          <li>
            <strong>Game Day ready.</strong> We take The Game seriously. Our rivalry tees take it
            slightly less seriously.
          </li>
        </ul>

        <h2>Come say hi</h2>
        <p>
          Find us at 57 Broadway, New Haven, CT 06511, or browse <Link to="/products">the full collection</Link>{' '}
          from the comfort of your dorm, office, or seminar you're definitely paying attention in.
        </p>
      </div>
    </section>
  )
}
