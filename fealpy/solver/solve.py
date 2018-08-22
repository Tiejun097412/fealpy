
import numpy as np
from scipy.sparse.linalg import cg, inv, dsolve, spsolve
from scipy.sparse import spdiags
from timeit import default_timer as timer
import pyamg
#import pylab

def solve1(a, L, uh, dirichlet=None, neuman=None, solver='cg'):
    space = a.space

    start = timer()
    A = a.get_matrix()
    b = L.get_vector()
    end = timer()

    print("Construct linear system time:", end - start)

    if neuman is not None:
        b += neuman.get_vector()

    if dirichlet is not None:
        AD, b = dirichlet.apply(A, b)
    else:
        AD = A

#    print("The condtion number is: ", np.linalg.cond(AD.todense()))
    if solver is 'cg':
        start = timer()
        D = AD.diagonal()
        M = spdiags(1/D, 0, AD.shape[0], AD.shape[1])
        uh[:], info = cg(AD, b, tol=1e-14, M=M)
        end = timer()
        print(info)
    elif solver is 'amg':
        start = timer()
        ml = pyamg.ruge_stuben_solver(AD)  
        uh[:] = ml.solve(b, tol=1e-12, accel='cg').reshape((-1,))
        end = timer()
        print(ml)
    elif solver is 'direct':
        start = timer()
        uh[:] = spsolve(AD, b)
        end = timer()
    else:
        print("We don't support solver: " + solver)

    print("Solve time:", end-start)

    return A 

def solve(dmodel, uh, dirichlet=None, solver='cg'):
    space = uh.space
    start = timer()
    A = dmodel.get_left_matrix()
    b = dmodel.get_right_vector()
    end = timer()

    print("Construct linear system time:", end - start)

    if dirichlet is not None:
        AD, b = dirichlet.apply(A, b)
    else:
        AD = A

    if solver is 'cg':
        start = timer()
        D = AD.diagonal()
        M = spdiags(1/D, 0, AD.shape[0], AD.shape[1])
        uh[:], info = cg(AD, b, tol=1e-14, M=M)
        end = timer()
        print(info)
    elif solver is 'amg':
        start = timer()
        ml = pyamg.ruge_stuben_solver(AD)  
        uh[:] = ml.solve(b, tol=1e-12, accel='cg').reshape(-1)
        end = timer()
        print(ml)
    elif solver is 'direct':
        start = timer()
        uh[:] = spsolve(AD, b)
        end = timer()
    else:
        raise ValueError("We don't support solver `{}`! ".format(solver))

    print("Solve time:", end-start)

    return AD, b 


def active_set_solver(dmodel, uh, gh, maxit=5000, dirichlet=None,
        solver='direct'):
    space = uh.space
    start = timer()
    A = dmodel.get_left_matrix()
    b = dmodel.get_right_vector()
    end = timer()
    print("Construct linear system time:", end - start)

    if dirichlet is not None:
        AD, b = dirichlet.apply(A, b)

    AD = AD.tolil()
    start = timer()
    lam = space.function()

    gdof = space.number_of_global_dofs()
    I = np.ones(gdof, dtype=np.bool)
    
    k = 0
    while k < maxit:
        print(k)
        k += 1
        I0 = I.copy()
        I[:] = (lam + gh - uh > 0)
        if np.all(I == I0) & (k > 1):
            break

        M = AD.copy()
        F = b.copy()

        idx, = np.nonzero(I)
        M[idx, :] = 0
        M[idx, idx] = 1
        F[idx] = gh[idx]

        if solver is 'direct':
            uh[:] = spsolve(M.tocsr(), F)
        elif solver is 'amg':
            ml = pyamg.ruge_stuben_solver(M.tocsr())  
            uh[:] = ml.solve(F, tol=1e-12, accel='cg').reshape(-1)
        lam[:] = AD@uh - b
    end = timer()
    print("Solve time:", end-start)
    return A, b


        
