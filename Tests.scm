(+ 1 3)

(* 1 2 3 4)

(define x 5)

(define y (quote (+ 1 2)))

(define square (lambda (x) (* x x)))
(define x (square x))

(define fact (lambda (n) (if (= n 0) 1 (* n (fact (- n 1))))))
(fact 5)

(and #f (define x 2))
x

(let ((x 5) (y 2)) (* x y))

