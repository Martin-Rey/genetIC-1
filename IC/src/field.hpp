//
// Created by Andrew Pontzen on 17/07/2016.
//

#ifndef IC_FIELD_HPP
#define IC_FIELD_HPP

#include <memory>
#include <vector>
#include <cassert>
#include "grid.hpp"

template<typename DataType, typename CoordinateType>
class Field : public std::enable_shared_from_this<Field<DataType, CoordinateType>> {
public:
  using TGrid = const Grid<CoordinateType>;
  using TPtrGrid = std::shared_ptr<TGrid>;
  using TData = std::vector<DataType>;
  using value_type = DataType;

protected:
  const TPtrGrid pGrid;
  TData data;
  bool fourier;

public:

  Field(TGrid & grid, TData && dataVector, bool fourier=true) : pGrid(grid.shared_from_this()),
                                                                data(std::move(dataVector)), fourier(fourier) {
    /*
     * Construct a field on the specified grid by moving the given data
     */
    assert(data.size()==grid.size3);

  }

  Field(TGrid & grid, const TData & dataVector, bool fourier=true) : pGrid(grid.shared_from_this()),
                                                                     data(dataVector), fourier(fourier) {
    /*
     * Construct a field on the specified grid by copying the given data
     */
    assert(data.size()==grid.size3);

  }

  Field(TGrid & grid, bool fourier=true) : pGrid(grid.shared_from_this()),
                                           data(grid.size3,0),
                                           fourier(fourier)
  {
    /*
     * Construct a zero-filled field on the specified grid
     */
  }

public:

  TGrid & getGrid() const {
    return const_cast<TGrid &>(*pGrid);
  }

  /*
   * ACCESS TO UNDERLYING DATA VECTOR
   */

  TData & getDataVector()  {
    return data;
  }

  const TData & getDataVector() const  {
    return data;
  }

  operator std::vector<DataType> &() {
    return getDataVector();
  }

  operator const std::vector<DataType> &() const {
    return getDataVector();
  }

  /*
   * EVALUATION OPERATIONS
   */

  DataType evaluateInterpolated(const Coordinate<CoordinateType> &location) const {
    auto offsetLower = pGrid->offsetLower;
    int x_p_0, y_p_0, z_p_0, x_p_1, y_p_1, z_p_1;


    // grid coordinates of parent cell starting to bottom-left
    // of our current point
    x_p_0 = (int) floor(((location.x - offsetLower.x) / pGrid->dx - 0.5));
    y_p_0 = (int) floor(((location.y - offsetLower.y) / pGrid->dx - 0.5));
    z_p_0 = (int) floor(((location.z - offsetLower.z) / pGrid->dx - 0.5));

    // grid coordinates of top-right
    x_p_1 = x_p_0 + 1;
    y_p_1 = y_p_0 + 1;
    z_p_1 = z_p_0 + 1;

    // weights, which are the distance to the centre point of the
    // upper-right cell, in grid units (-> maximum 1)

    CoordinateType xw0, yw0, zw0, xw1, yw1, zw1;
    xw0 = ((CoordinateType) x_p_1 + 0.5) - ((location.x - offsetLower.x) / pGrid->dx);
    yw0 = ((CoordinateType) y_p_1 + 0.5) - ((location.y - offsetLower.y) / pGrid->dx);
    zw0 = ((CoordinateType) z_p_1 + 0.5) - ((location.z - offsetLower.z) / pGrid->dx);

    xw1 = 1. - xw0;
    yw1 = 1. - yw0;
    zw1 = 1. - zw0;

    assert(xw0 <= 1.0 && xw0 >= 0.0);

    // allow things on the boundary to 'saturate' value, but beyond boundary
    // is not acceptable
    //
    // TODO - in some circumstances we may wish to replace this with wrapping
    // but not all circumstances!
    int size_i = static_cast<int>(pGrid->size);
    assert(x_p_1 <= size_i);
    if (x_p_1 == size_i) x_p_1 = size_i - 1;
    assert(y_p_1 <= size_i);
    if (y_p_1 == size_i) y_p_1 = size_i - 1;
    assert(z_p_1 <= size_i);
    if (z_p_1 == size_i) z_p_1 = size_i - 1;

    assert(x_p_0 >= -1);
    if (x_p_0 == -1) x_p_0 = 0;
    assert(y_p_0 >= -1);
    if (y_p_0 == -1) y_p_0 = 0;
    assert(z_p_0 >= -1);
    if (z_p_0 == -1) z_p_0 = 0;


    return xw0 * yw0 * zw1 * (*this)[pGrid->getCellIndexNoWrap(x_p_0, y_p_0, z_p_1)] +
           xw1 * yw0 * zw1 * (*this)[pGrid->getCellIndexNoWrap(x_p_1, y_p_0, z_p_1)] +
           xw0 * yw1 * zw1 * (*this)[pGrid->getCellIndexNoWrap(x_p_0, y_p_1, z_p_1)] +
           xw1 * yw1 * zw1 * (*this)[pGrid->getCellIndexNoWrap(x_p_1, y_p_1, z_p_1)] +
           xw0 * yw0 * zw0 * (*this)[pGrid->getCellIndexNoWrap(x_p_0, y_p_0, z_p_0)] +
           xw1 * yw0 * zw0 * (*this)[pGrid->getCellIndexNoWrap(x_p_1, y_p_0, z_p_0)] +
           xw0 * yw1 * zw0 * (*this)[pGrid->getCellIndexNoWrap(x_p_0, y_p_1, z_p_0)] +
           xw1 * yw1 * zw0 * (*this)[pGrid->getCellIndexNoWrap(x_p_1, y_p_1, z_p_0)];
  }

  DataType operator[](size_t i) const  {
    return data[i];
  }

  /*
   * FOURIER TRANSFORM SUPPORT
   */

  template<typename T>
  void matchFourier(const T & other) {
    if(other.isFourier())
      toFourier();
    else
      toReal();
  }

  bool isFourier() const {
    return fourier;
  }

  void toFourier()  {
    if(fourier) return;
    fft(data.data(), data.data(), this->pGrid->size, 1);
    fourier=true;
  }

  void toReal()  {
    if(!fourier) return;
    fft(data.data(), data.data(), this->pGrid->size, -1);
    fourier=false;
  }

  void addFieldFromDifferentGrid(const Field<DataType, CoordinateType> & source) {
    assert(!source.isFourier());
    toReal();
    TPtrGrid pSourceProxyGrid = source.getGrid().makeProxyGridToMatch(getGrid());


    size_t size3 = getGrid().size3;

#pragma omp parallel for schedule(static)
    for (size_t ind_l = 0; ind_l < size3; ind_l++) {
      if (pSourceProxyGrid->containsCell(ind_l))
        data[ind_l] += pSourceProxyGrid->getFieldAt(ind_l, source);
    }

  }

  void addFieldFromDifferentGrid(Field<DataType, CoordinateType> & source) {
    source.toReal();
    addFieldFromDifferentGrid(const_cast<const Field<DataType,CoordinateType> &>(source));
  }

};



#endif //IC_FIELD_HPP