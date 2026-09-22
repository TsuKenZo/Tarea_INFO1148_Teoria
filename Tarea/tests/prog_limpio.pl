% Hechos - comentario de linea
padre(juan, ana).
padre(juan, pedro).
madre('Juan Pérez', ana).
madre(':-', hija).

/* comentario
   de bloque */
abuelo(X, Z) :-
    padre(X, Y),
    padre(Y, Z).

edad(juan, 25).
valor(pi, 3.14).
negativo(-5).
texto("hola").
texto2("ok\x").
atomo_esc('ok\a').

comp(X) :- X == Y, X \= Z, A =.. B, C =< D, E >= F, G < H, I > J, K = L, M \== N.
arit(R) :- R is 5 + 3 * 2 - 4 / 2 // 1 ** 2 mod 3.
ctrl :- \+ fail, ! ; true.
lista([a, b | R]).
registro({a}).
anon(_, _Tmp).
?- abuelo(juan, Quien).
regla --> terminal.
resta(X) :- Y is X - 3.
neg_ctx(X) :- Y is -5.
