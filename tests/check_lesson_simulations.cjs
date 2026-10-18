const assert = require('node:assert/strict');
const E = require('../assets/lesson-simulations.js');
const fs = require('node:fs');
for (const grade of [6,7,9]) {
  const data = JSON.parse(fs.readFileSync(`${__dirname}/../${grade}/simulations.json`));
  for (const lesson of data.lessons) for (const game of lesson.games) {
    let state = E.createState(game);
    assert.equal(E.choose(game, state, -1), state);
    for (const [i, step] of game.steps.entries()) {
      const bad = step.choices.findIndex(c => c.effect === 'retry');
      const good = step.choices.findIndex(c => c.effect === 'advance');
      const paused = {...state, paused:true};
      assert.equal(E.choose(game, paused, good), paused);
      state = E.choose(game, state, bad);
      assert.equal(state.first[i], false);
      if (game.mode === 'learn') {
        assert.equal(state.phase, 'playing');
        state = E.choose(game, state, good);
        assert.equal(state.first[i], false, 'retry must not erase first choice');
      } else assert.equal(E.choose(game, state, good), state, 'check locks first choice');
      assert.equal(state.phase, 'accepted');
      state = E.advance(game, state);
    }
    assert.equal(state.phase, 'complete');
    assert.equal(state.firstResult, 0);
    assert.equal(E.score(state), 0);
    assert.deepEqual(E.createState(game, JSON.parse(JSON.stringify(state))), state);
    state = E.restart(game, state);
    for (const step of game.steps) {
      state = E.advance(game, E.choose(game, state, step.choices.findIndex(c => c.effect === 'advance')));
    }
    assert.equal(E.score(state), 2);
    assert.equal(state.firstResult, 0, 'replay preserves original completed score');
    for (const corrupt of [{cursor:90}, {first:[]}, {run:'x'}, {lastChoice:99}, {paused:'false'}, {signature:'old'}])
      assert.deepEqual(E.createState(game, {...state,...corrupt}), E.createState(game));
  }
}
console.log('PASS: 768 games: retry, first-choice scoring, pause, persistence, replay, corrupt state');
