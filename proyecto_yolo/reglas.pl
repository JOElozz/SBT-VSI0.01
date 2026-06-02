% EPP requerido por fase
epp_requerido(cabeza, [helmet, glass]).
epp_requerido(torso,  [vest]).
epp_requerido(manos,  [glove]).
epp_requerido(botas,  [boots]).

% Verificar si todos los elementos requeridos fueron detectados
fase_aprobada(Zona, Detectados) :-
    epp_requerido(Zona, Requeridos),
    maplist(member_check(Detectados), Requeridos).

member_check(Lista, Elemento) :-
    member(Elemento, Lista).