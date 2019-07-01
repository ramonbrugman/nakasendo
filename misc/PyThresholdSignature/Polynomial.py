#!/usr/bin/env python3

#################################################################
#  Date             28/06/2019                                  #
#  Author           nChain's employees                          #
#                                                               #
#  Copyright (c) 2019 nChain Limited. All rights reserved       #
#################################################################
import random
import FiniteGroup

"""
Polynomial of degree N is defined an array of (N+1) coefficient
Lagrange polynomial is a suite of polynomial indexing from 0 to N, determined by an array of N+1 points ( x,f(x))
"""

class Polynomial:
    """Polynomial of degree N is defined an array of (N+1) coefficient"""
    def __init__(self, coeffs_array=None, group_modulo=None):
        self.q=None
        self.a=[]
        if coeffs_array:
            self.a=coeffs_array
        if group_modulo:
            self.q=group_modulo
            self.__normalize()

    def degree(self):
        return len(self.a)-1

    def __repr__(self):
        outstr = 'Polynomial modulo : {}\n'.format(self.q if self.q else 'None')
        if not self.a:
            outstr+='empty coeff'
        else:
            for i in range (len(self.a)):
                outstr += '  a_{}={}\n'.format(i, self.a[i])
        return outstr

    def set_group_modulo(self, group_modulo):
        self.q = group_modulo
        self.__normalize()

    def append_coeff(self, a_i):
        coeff = FiniteGroup.normalize_mod(a_i, self.q) if self.q else a_i
        self.a.append(coeff)

    # evaluate polynomial at value x
    def __call__(self, x):
        if not self.a:
            raise RuntimeError('Unable to evaluate polynomial when it is empty')
        if self.a[-1]==0:
            raise RuntimeWarning('Polynomial has zero coefficient at the highest degree')

        ret=0
        x_k=1 ## x^k
        for k in range (len(self.a)):
            a_k = self.a[k]
            x_k = FiniteGroup.normalize_mod(x_k, self.q) if self.q else x_k
            ret += FiniteGroup.normalize_mod(a_k*x_k, self.q) if self.q else a_k*x_k
            x_k*=x
        return FiniteGroup.normalize_mod(ret, self.q) if self.q else ret

    def __normalize(self):
        if not self.q:
            raise RuntimeError('Unable to normalize polynomial while group modulo is not determined')
        if self.a:
            self.a = [FiniteGroup.normalize_mod(a_i, self.q) for a_i in self.a]

    #def __add__(self, other):
    #    ## Check compatibility of degree, modulo ...
    #    if self.degree() != other.degree():
    #        raise TypeError('Add polynomial of incompatible degree ')

def RandomPolynomial(degree=1, modulo=None):
    if degree<1:
        raise RuntimeError('Unable to generate polynomial with degree less than 1')
    default_max_bound = modulo if modulo else 100
    coeffs=[]
    a_0=-1 # Get a_0 that must be strictly positive
    while a_0 < 0:
        a_0 = FiniteGroup.generate_random_positive_mod(default_max_bound)
    coeffs.append(a_0)
    while degree>0:
        degree=degree-1
        a_k = FiniteGroup.generate_random_positive_mod(default_max_bound)
        coeffs.append(a_k)
    while coeffs[-1]==0:## fix the last coefficient (highest degree) should be non null
        coeffs[len(coeffs)-1] = FiniteGroup.generate_random_positive_mod(default_max_bound)
    return Polynomial(coeffs, modulo) if  modulo else Polynomial(coeffs)

class LagrangeInterpolator:
    r"""
        Lagrange interpolator is a set of N+1 points [x,f(x)]
        It implicitly define N+1 interpolator polynomials indexed from 0 to N, each of which have degree N
        Lagrange interpolator is a set of N polynomials that can evaluate at any point x
          Assuming a Lagrange interpolator is L, user can do
            L(x) to evaluate the interpolated value at x
            L[i](x) to evaluate the ith basis of Lagrange polynomial at x

            f(x) = \sum_{i} f_i L_i(x)  = \sum_{i} f(x_i) L_i(x)
            L_i(x) = \prod_{j \neq i} \frac{x - x_j}{x_i - x_j}
    """
    def __init__(self, points=None, group_modulo=None):
        self.xfx=[]
        self.q=None
        if points:
            self.xfx=points
        if group_modulo:
            self.q=group_modulo
            self.__normalize()
        self.__i=None# index of the lagrangian polynomial basis, when it is non null, it become the i-th Lagrangian polynomial
        if self.xfx and len(self.xfx) >1:
            if self.q:
                self.__normalize()
            if not self.__is_well_defined():
                print(self.__repr__())
                raise RuntimeError('Lagrangian polynomial bad defined')

    def degree(self):
        return len(self.xfx)-1

    ## Append point only to the general interpolator.
    def append_point(self, xfx_i):
        if self.__i:
            raise RuntimeError('A particular ith Lagrangian polynomial basis cannot add points')

        _x = FiniteGroup.normalize_mod(xfx_i[0], self.q) if self.q else xfx_i[0]
        _fx = FiniteGroup.normalize_mod(xfx_i[1], self.q) if self.q else xfx_i[1]
        self.xfx.append([_x,_fx])

        if len(self.xfx) > 1 and not self.__is_well_defined():
            print(self.__repr__())
            raise RuntimeError('Lagrangian polynomial bad defined')

    def degree(self):
        return len(self.xfx)-1

    def __repr__(self):
        outstr = 'Lagrange polynomial modulo : {}\n'.format(self.q if self.q else 'None')
        if self.__i:
            outstr+='   basis index [{}]'.format(self.__i)
        if not self.xfx:
            outstr+='empty lagrange'
        else:
            for i in range (len(self.xfx)):
                outstr += '  [x_{}, f_{}]=[{},{}]\n'.format(i,i, self.xfx[i][0],self.xfx[i][1])
        return outstr

    def set_group_modulo(self, group_modulo):
        self.q = group_modulo
        self.__normalize()

    # evaluate polynomial at value x
    def __call__(self, x):
        if not self.xfx or len(self.xfx)<2:
            raise RuntimeError('Unable to evaluate lagrangian polynomial with less than 2 points')
        if self.__i and (self.__i<0 or self.__i>=len(self.xfx)):
            raise RuntimeWarning('Inappropriate index {} for lagrange polynomial of degree {}'.format(self.__i, self.degree()))

        if self.__i is not None:## If its a basis Lagrange polynomial, evaluate its ith basis
            return self.__eval_Li(self.__i, x)
        sum=0
        for i in range(len(self.xfx)):
            L_i_x = self.__eval_Li(i, x)
            sum += self.xfx[i][1]* L_i_x

        sum = FiniteGroup.normalize_mod(sum, self.q) if self.q else sum
        return sum

    def __getitem__(self, l_index):
        if l_index < 0 or l_index >= len(self.xfx):
            raise RuntimeError('Get L_{} with bad index'.format(l_index))
        newLagrange = LagrangeInterpolator(self.xfx, self.q)
        newLagrange.__i = l_index
        return newLagrange

    def __normalize(self):
        if not self.q:
            raise RuntimeError('Unable to normalize lagrange polynomial while group modulo is not determined')
        if self.xfx:
            self.xfx = [[FiniteGroup.normalize_mod(xfx_i[0], self.q), FiniteGroup.normalize_mod(xfx_i[1], self.q)] for xfx_i in self.xfx]

    ## Lagrange polynomial requires :
    ##   All x_i should be different
    ##   The index of the Lagrange basis if exist, should be less than or equal to the degree of the polynomial
    def __is_well_defined(self):
        if self.__i and (self.__i < 0 or self.__i >= len(self.xfx)):
            return False
        if not self.xfx or len(self.xfx) < 2:
            return False
        xvals=set()
        for i in range (len(self.xfx)):
            if self.xfx[i][0] not in xvals:
                xvals.add(self.xfx[i][0])
            else:
                return False
        return True

    def __eval_Li(self,i,x):
        #L_i(x) = \prod_{j \neq i} \frac{x - x_j}{x_i - x_j}

        if i<0 or i>=len(self.xfx):
            raise RuntimeError('Eval L_{} with bad index'.format(i))
        mul=1
        for j in range(len(self.xfx)):
            if j==i:
                continue
            raw_mumerator = x - self.xfx[j][0]
            raw_denominator = self.xfx[i][0] - self.xfx[j][0]
            mumerator = FiniteGroup.normalize_mod(raw_mumerator, self.q) if self.q else raw_mumerator
            denominator = FiniteGroup.normalize_mod(raw_denominator, self.q) if self.q else raw_denominator
            raw_term = mumerator * FiniteGroup.inv_mod(denominator, self.q) if self.q else mumerator/denominator
            term = FiniteGroup.normalize_mod(raw_term, self.q) if self.q else raw_term
            mul *= term
        mul = FiniteGroup.normalize_mod(mul, self.q) if self.q else mul
        return mul

